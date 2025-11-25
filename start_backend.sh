lsof -ti:8006 | xargs kill -9 && lsof -ti:3000 | xargs kill -9
pkill -9 -f "python main.py"
cd /Users/vishnuvardhanmedara/DayTraderAI/backend && source venv/bin/activate && python main.py

