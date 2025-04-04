import psycopg2

def setup_database(config):
    """Set up the database connection."""
    try:
        # Generate database connection string
        db_connection_string = f"postgresql://{config['POSTGRES_USER']}:{config['POSTGRES_PASSWORD']}@{config['DB_HOST']}:{config['DB_PORT']}/{config['DB_NAME']}"
        print(f"Database connection string: {db_connection_string}")
        
        # Setup the database connection
        conn = psycopg2.connect(
            dbname=config['DB_NAME'],
            user=config['POSTGRES_USER'],
            password=config['POSTGRES_PASSWORD'],
            host=config['DB_HOST'],
            port=config['DB_PORT']
        )
        print(f"Connected to PostgreSQL database: {config['DB_NAME']} on {config['DB_HOST']}:{config['DB_PORT']}")
        
        # Create the test database if necessary
        if config['DB_ENV'] == "TESTING":
            create_test_database(config)
        
        return conn
    
    except Exception as e:
        print(f"Failed to connect to database: {e}")
        exit(1)

def create_test_database(config):
    """Create test database if it doesn't exist."""
    try:
        # Connect to default postgres database
        postgres_conn = psycopg2.connect(
            dbname="postgres",
            user=config['POSTGRES_USER'],
            password=config['POSTGRES_PASSWORD'],
            host='localhost',
            port='5432'
        )
        postgres_conn.autocommit = True
        
        with postgres_conn.cursor() as cursor:
            # Check if database exists
            cursor.execute(f"SELECT 1 FROM pg_database WHERE datname = '{config['DB_NAME']}'")
            exists = cursor.fetchone()
            
            if not exists:
                print(f"Creating test database: {config['DB_NAME']}")
                cursor.execute(f"CREATE DATABASE {config['DB_NAME']}")
                
        postgres_conn.close()
    except Exception as e:
        print(f"Could not create test database: {e}")