class Config: 
    SECRET_KEY = 'Group16Assignment!'
    SQLALCHEMY_DATABASE_URI = 'postgresql://postgres.vvbfnkmgyebcnhqdamxd:Group16Assignment!@aws-0-eu-central-1.pooler.supabase.com:6543/postgres'
    SQLALCHEMY_TRACK_MODIFICATIONS = False


    # Flask-Mail Configuratie
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USE_SSL = False
    MAIL_USERNAME = 'dishcovery101@gmail.com'  
    MAIL_PASSWORD = 'rydu ueej ftbr izpb'
    MAIL_DEFAULT_SENDER = 'dishcovery101@gmail.com'


 