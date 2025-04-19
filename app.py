from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
import os
import asyncio
import threading
import logging
from datetime import datetime
from urllib.parse import urlparse as url_parse
from dotenv import load_dotenv
from gemini_client import GeminiClient
from models import db, User, BotCommand, BotConfig, LogEntry
from bot import run_bot
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from forms import LoginForm, RegistrationForm

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "gemini-discord-bot-secret")

# Configure database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
db.init_app(app)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access the dashboard.'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    """Load user by ID."""
    return User.query.get(int(user_id))

# Initialize Gemini client if API key is available
gemini_client = None
gemini_api_key = os.environ.get("GEMINI_API_KEY", "")
if gemini_api_key:
    gemini_client = GeminiClient(api_key=gemini_api_key)

# Global variable to store bot thread
bot_thread = None
# In-memory store for the latest logs
latest_logs = []
# Global bot state
bot_running = False

def log_to_db(level, message, source="WEB"):
    """Add a log entry to the database and in-memory store"""
    try:
        with app.app_context():
            log_entry = LogEntry(log_level=level, message=message, source=source)
            db.session.add(log_entry)
            db.session.commit()
            # Add to in-memory store (limit to 100 entries)
            latest_logs.append({
                'level': level,
                'message': message,
                'timestamp': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
                'source': source
            })
            if len(latest_logs) > 100:
                latest_logs.pop(0)
    except Exception as e:
        logger.error(f"Failed to add log entry: {str(e)}")

def run_discord_bot():
    """Function to run the Discord bot in a separate thread"""
    global bot_running
    try:
        bot_running = True
        log_to_db("INFO", "Starting Discord bot...")
        asyncio.run(run_bot(config_from_db=True, log_callback=log_to_db))
    except Exception as e:
        error_msg = f"Discord bot error: {str(e)}"
        logger.error(error_msg)
        log_to_db("ERROR", error_msg)
    finally:
        bot_running = False

def start_bot_if_configured():
    """Start the bot if API keys are configured"""
    global bot_thread, bot_running
    
    # Check if bot is already running
    if bot_thread and bot_thread.is_alive():
        return "Bot is already running"
    
    # Check if API keys are configured
    discord_token = os.environ.get("DISCORD_TOKEN")
    gemini_api_key = os.environ.get("GEMINI_API_KEY")
    
    if not discord_token or not gemini_api_key:
        log_to_db("ERROR", "Cannot start bot: Missing API keys")
        return "Cannot start bot: Missing API keys"
    
    # Start bot in a new thread
    bot_thread = threading.Thread(target=run_discord_bot)
    bot_thread.daemon = True  # Thread will exit when main program exits
    bot_thread.start()
    
    return "Bot started successfully"

# Initialize the database
with app.app_context():
    db.create_all()
    # Add default settings if they don't exist
    default_settings = [
        {"name": "command_prefix", "value": "!", "description": "Prefix for bot commands"},
        {"name": "response_temperature", "value": "0.7", "description": "Temperature for Gemini AI responses"},
        {"name": "max_response_length", "value": "2000", "description": "Maximum length for each message chunk"}
    ]
    
    for setting in default_settings:
        existing = BotConfig.query.filter_by(setting_name=setting["name"]).first()
        if not existing:
            new_setting = BotConfig(
                setting_name=setting["name"],
                setting_value=setting["value"],
                setting_description=setting["description"]
            )
            db.session.add(new_setting)
    
    # Check if admin user exists, if not create one
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(
            username='admin',
            email='admin@example.com',
            is_admin=True
        )
        admin.set_password('adminpassword')  # Default password, should be changed immediately
        db.session.add(admin)
        log_to_db("INFO", "Created default admin user")
    
    try:
        db.session.commit()
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")

# Routes
@app.route('/')
def index():
    """Render the home page"""
    return render_template('index.html')

@app.route('/api/ask', methods=['POST'])
async def ask():
    """API endpoint to ask a question to Gemini AI"""
    if not gemini_client:
        return jsonify({
            'success': False, 
            'message': 'Gemini API key not configured. Please set the GEMINI_API_KEY environment variable.'
        }), 500
    
    data = request.json
    question = data.get('question', '')
    
    if not question:
        return jsonify({
            'success': False, 
            'message': 'Please provide a question.'
        }), 400
    
    try:
        response = await gemini_client.generate_response(question)
        return jsonify({
            'success': True, 
            'response': response
        })
    except Exception as e:
        error_msg = f"Error generating response: {str(e)}"
        log_to_db("ERROR", error_msg)
        return jsonify({
            'success': False, 
            'message': error_msg
        }), 500

@app.route('/setup')
def setup():
    """Render setup instructions page"""
    return render_template('setup.html')

@app.route('/docs')
def docs():
    """Render documentation page"""
    return render_template('docs.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login."""
    # If user is already logged in, redirect to dashboard
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            log_to_db("INFO", f"User {user.username} logged in")
            
            # Redirect to the page the user was trying to access
            next_page = request.args.get('next')
            if not next_page or url_parse(next_page).netloc != '':
                next_page = url_for('dashboard')
            
            flash('Login successful!', 'success')
            return redirect(next_page)
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template('login.html', form=form)

@app.route('/logout')
def logout():
    """Handle user logout."""
    if current_user.is_authenticated:
        log_to_db("INFO", f"User {current_user.username} logged out")
        logout_user()
        flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Handle user registration."""
    # If user is already logged in, redirect to dashboard
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data
        )
        user.set_password(form.password.data)
        
        db.session.add(user)
        db.session.commit()
        
        log_to_db("INFO", f"New user registered: {user.username}")
        flash('Registration successful! You can now log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html', form=form)

@app.route('/dashboard')
@login_required
def dashboard():
    """Render the dashboard page"""
    configs = BotConfig.query.all()
    commands = BotCommand.query.all()
    
    # Get commands created by the current user
    if not current_user.is_admin:
        commands = BotCommand.query.filter_by(user_id=current_user.id).all()
    
    # Get API key status
    discord_token = bool(os.environ.get("DISCORD_TOKEN"))
    gemini_api_key = bool(os.environ.get("GEMINI_API_KEY"))
    
    return render_template(
        'dashboard.html', 
        configs=configs, 
        commands=commands,
        bot_running=bot_running,
        discord_token=discord_token,
        gemini_api_key=gemini_api_key,
        latest_logs=latest_logs[-20:]  # Show the last 20 logs
    )

@app.route('/dashboard/bot/start', methods=['POST'])
@login_required
def start_bot():
    """Start the Discord bot"""
    # Only admins can start the bot
    if not current_user.is_admin:
        flash('You do not have permission to start the bot.', 'danger')
        return redirect(url_for('dashboard'))
    result = start_bot_if_configured()
    flash(result, 'success' if 'successfully' in result else 'danger')
    return redirect(url_for('dashboard'))

@app.route('/dashboard/bot/stop', methods=['POST'])
@login_required
def stop_bot():
    """Stop the Discord bot (not implemented - would require restart)"""
    # Only admins can stop the bot
    if not current_user.is_admin:
        flash('You do not have permission to stop the bot.', 'danger')
        return redirect(url_for('dashboard'))
    flash("Stopping the bot is not supported. The bot will stop when the application is restarted.", "warning")
    return redirect(url_for('dashboard'))

@app.route('/dashboard/commands', methods=['GET', 'POST'])
@login_required
def manage_commands():
    """Manage custom bot commands"""
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'add':
            command_name = request.form.get('command_name')
            command_description = request.form.get('command_description')
            response_template = request.form.get('response_template')
            
            # Validate input
            if not command_name or not response_template:
                flash('Command name and response template are required', 'danger')
                return redirect(url_for('manage_commands'))
            
            # Check if command already exists
            existing = BotCommand.query.filter_by(command_name=command_name).first()
            if existing:
                flash(f'Command "{command_name}" already exists', 'danger')
                return redirect(url_for('manage_commands'))
            
            # Create new command
            new_command = BotCommand(
                command_name=command_name,
                command_description=command_description or '',
                response_template=response_template,
                is_active=True,
                user_id=current_user.id  # Associate with current user
            )
            
            db.session.add(new_command)
            db.session.commit()
            
            log_to_db("INFO", f"Added new command: {command_name} by user {current_user.username}")
            flash(f'Command "{command_name}" added successfully', 'success')
        
        elif action == 'delete':
            command_id = request.form.get('command_id')
            command = BotCommand.query.get(command_id)
            
            # Check if user owns this command or is admin
            if command and (command.user_id == current_user.id or current_user.is_admin):
                db.session.delete(command)
                db.session.commit()
                log_to_db("INFO", f"Deleted command: {command.command_name} by user {current_user.username}")
                flash(f'Command "{command.command_name}" deleted', 'success')
            else:
                flash('Command not found or you do not have permission to delete it', 'danger')
        
        elif action == 'toggle':
            command_id = request.form.get('command_id')
            command = BotCommand.query.get(command_id)
            
            # Check if user owns this command or is admin
            if command and (command.user_id == current_user.id or current_user.is_admin):
                command.is_active = not command.is_active
                db.session.commit()
                status = "activated" if command.is_active else "deactivated"
                log_to_db("INFO", f"Command {command.command_name} {status} by user {current_user.username}")
                flash(f'Command "{command.command_name}" {status}', 'success')
            else:
                flash('Command not found or you do not have permission to modify it', 'danger')
        
        return redirect(url_for('manage_commands'))
    
    # GET request
    if current_user.is_admin:
        # Admins can see all commands
        commands = BotCommand.query.all()
    else:
        # Regular users can only see their own commands
        commands = BotCommand.query.filter_by(user_id=current_user.id).all()
        
    return render_template('commands.html', commands=commands)

@app.route('/dashboard/config', methods=['GET', 'POST'])
@login_required
def manage_config():
    """Manage bot configuration"""
    # Only admins can access this page
    if not current_user.is_admin:
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        for key, value in request.form.items():
            if key.startswith('config_'):
                setting_id = key.replace('config_', '')
                config = BotConfig.query.get(setting_id)
                
                if config and config.setting_value != value:
                    old_value = config.setting_value
                    config.setting_value = value
                    log_to_db("INFO", f"Updated config {config.setting_name}: {old_value} -> {value}")
        
        db.session.commit()
        flash('Configuration updated successfully', 'success')
        return redirect(url_for('manage_config'))
    
    # GET request
    configs = BotConfig.query.all()
    return render_template('config.html', configs=configs)

@app.route('/dashboard/logs')
@login_required
def view_logs():
    """View bot logs"""
    # Only admins can view all logs
    if not current_user.is_admin:
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('dashboard'))
    page = request.args.get('page', 1, type=int)
    logs_query = LogEntry.query.order_by(LogEntry.timestamp.desc())
    logs_pagination = logs_query.paginate(page=page, per_page=50)
    
    return render_template('logs.html', logs=logs_pagination)

@app.route('/dashboard/api-keys', methods=['GET', 'POST'])
@login_required
def manage_api_keys():
    """Manage API keys"""
    # Only admins can manage API keys
    if not current_user.is_admin:
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        discord_token = request.form.get('discord_token')
        gemini_api_key = request.form.get('gemini_api_key')
        
        if discord_token:
            os.environ['DISCORD_TOKEN'] = discord_token
            with open('.env', 'r') as f:
                env_lines = f.readlines()
            
            with open('.env', 'w') as f:
                for line in env_lines:
                    if line.startswith('DISCORD_TOKEN='):
                        f.write(f'DISCORD_TOKEN={discord_token}\n')
                    else:
                        f.write(line)
            
            log_to_db("INFO", "Updated Discord API token")
            flash('Discord API token updated', 'success')
        
        if gemini_api_key:
            os.environ['GEMINI_API_KEY'] = gemini_api_key
            with open('.env', 'r') as f:
                env_lines = f.readlines()
            
            with open('.env', 'w') as f:
                for line in env_lines:
                    if line.startswith('GEMINI_API_KEY='):
                        f.write(f'GEMINI_API_KEY={gemini_api_key}\n')
                    else:
                        f.write(line)
            
            # Reinitialize Gemini client
            global gemini_client
            gemini_client = GeminiClient(api_key=gemini_api_key)
            
            log_to_db("INFO", "Updated Gemini API key")
            flash('Gemini API key updated', 'success')
        
        return redirect(url_for('manage_api_keys'))
    
    # GET request
    discord_token_set = bool(os.environ.get('DISCORD_TOKEN'))
    gemini_api_key_set = bool(os.environ.get('GEMINI_API_KEY'))
    
    return render_template(
        'api_keys.html', 
        discord_token_set=discord_token_set,
        gemini_api_key_set=gemini_api_key_set
    )

@app.route('/api/logs/latest')
def get_latest_logs():
    """API endpoint to get the latest logs"""
    return jsonify(latest_logs[-20:])

if __name__ == '__main__':
    # Try to start the bot if possible
    start_bot_if_configured()
    
    # Run the Flask app
    app.run(host='0.0.0.0', port=5000, debug=True)