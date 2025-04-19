from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(UserMixin, db.Model):
    """Model for user accounts."""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    commands = db.relationship('BotCommand', backref='creator', lazy='dynamic')
    
    def set_password(self, password):
        """Set the user's password hash."""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check if the provided password matches the stored hash."""
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'

class BotCommand(db.Model):
    """Model for custom bot commands configured through the dashboard."""
    id = db.Column(db.Integer, primary_key=True)
    command_name = db.Column(db.String(50), nullable=False, unique=True)
    command_description = db.Column(db.String(200), nullable=False)
    response_template = db.Column(db.Text, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    def __repr__(self):
        return f'<BotCommand {self.command_name}>'

class BotConfig(db.Model):
    """Model for storing bot configuration settings."""
    id = db.Column(db.Integer, primary_key=True)
    setting_name = db.Column(db.String(50), nullable=False, unique=True)
    setting_value = db.Column(db.Text, nullable=True)
    setting_description = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<BotConfig {self.setting_name}>'

class LogEntry(db.Model):
    """Model for storing bot logs and errors."""
    id = db.Column(db.Integer, primary_key=True)
    log_level = db.Column(db.String(20), nullable=False, default='INFO')
    message = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    source = db.Column(db.String(50), nullable=True)
    
    def __repr__(self):
        return f'<LogEntry {self.log_level} {self.timestamp}>'