import secrets
import os
import argparse

def main():
    parser = argparse.ArgumentParser(description='Generate Gaatha Suite secret keys.')
    parser.add_argument('--instance', action='store_true', help='Write to instance/.env')
    args = parser.parse_args()

    key = secrets.token_urlsafe(64)
    env_line = f"SECRET_KEY={key}\n"
    
    # Update root .env
    with open('.env', 'a+') as f:
        f.write(env_line)
    print("✅ Generated new secret and updated .env")

    if args.instance:
        os.makedirs('instance', exist_ok=True)
        with open('instance/.env', 'a+') as f:
            f.write(env_line)
        print("✅ Updated instance/.env")

if __name__ == '__main__':
    main()