def setup_tables(conn, table_name):
    """Set up the database tables."""
    try:
        with conn.cursor() as cursor:
            # First, check if the table exists and what columns it has
            cursor.execute(f"""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = '{table_name}'
            """)
            columns = cursor.fetchall()
            print(f"Existing columns in {table_name}: {columns}")
            
            if not columns:
                # Create the table if it doesn't exist
                cursor.execute(f"""
                    CREATE TABLE IF NOT EXISTS {table_name} (
                        id SERIAL PRIMARY KEY,
                        temperature FLOAT NOT NULL,
                        humidity FLOAT NOT NULL,
                        light FLOAT NOT NULL,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                conn.commit()
                print(f"Table '{table_name}' created with columns: id, temperature, humidity, light, timestamp")
            else:
                print(f"Table '{table_name}' already exists with columns: {columns}")
    except Exception as e:
        print(f"Failed to configure table: {e}")
        exit(1)

def insert_sensor_data(conn, table_name, temperature, humidity, light):
    """Insert sensor data into the database."""
    try:
        with conn.cursor() as cursor:
            cursor.execute(f"""
                INSERT INTO {table_name} (temperature, humidity, light) 
                VALUES (%s, %s, %s)
            """, (temperature, humidity, light))
            conn.commit()
            print(f"Data inserted into database: temp={temperature}, humidity={humidity}, light={light}")
        return True
    except Exception as e:
        print(f"Error inserting data: {e}")
        return False

def get_recent_sensor_data(conn, table_name, limit=100):
    """Retrieve recent sensor data from the database."""
    try:
        with conn.cursor() as cursor:
            cursor.execute(f"""
                SELECT temperature, humidity, light, timestamp 
                FROM {table_name} 
                ORDER BY timestamp DESC 
                LIMIT %s
            """, (limit,))
            records = cursor.fetchall()
            return records
    except Exception as e:
        print(f"Error retrieving data: {e}")
        return []