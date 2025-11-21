# Password Strength Checker

A web application with two pages: Welcome page and Password Checker with AI chat.

## Features
- Welcome page with "Go" button
- Password strength checker showing percentage
- Generate new password button
- Real-time AI chat assistant
- Works in all browsers

## Local Development

```bash
pip install -r requirements.txt
python api/index.py
```

Visit: `http://127.0.0.1:5000`

## Deploy to Vercel

1. Push code to GitHub:
```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USERNAME/password-checker.git
git push -u origin main
```

2. Go to [vercel.com](https://vercel.com)
3. Click "New Project"
4. Import your GitHub repository
5. Vercel will auto-detect the configuration
6. Click "Deploy"

Your app will be live at: `https://your-project-name.vercel.app`

## Project Structure

```
.
├── api/
│   └── index.py          # Main Flask app
├── vercel.json           # Vercel configuration
├── requirements.txt      # Python dependencies
├── .gitignore           # Git ignore file
└── README.md            # This file
```
