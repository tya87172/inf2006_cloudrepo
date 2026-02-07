@"
#!/bin/bash
set -e

echo "Starting deployment..."

cd /home/ec2-user/project

echo "Installing Python dependencies..."
python3 -m pip install --user -r requirements.txt

echo "Building frontend..."
cd frontend
npm install
npm run build
cd ..

echo "Updating database..."
python3 backend/db/init_db.py

echo "Restarting service..."
sudo systemctl restart coe-analytics || echo "Service not yet configured"

echo "Deployment complete!"
"@ | Out-File -FilePath "deploy.sh" -Encoding UTF8