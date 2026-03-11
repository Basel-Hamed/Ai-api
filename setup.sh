#!/data/data/com.termux/files/usr/bin/bash
# setup.sh

echo "🔧 প্রাইভেট ওয়েবসাইট API সেটআপ"
echo "=================================="

# আপডেট
echo "📦 প্যাকেজ আপডেট হচ্ছে..."
pkg update -y && pkg upgrade -y

# পাইথন
echo "🐍 পাইথন ইনস্টল হচ্ছে..."
pkg install python -y

# পাইথন প্যাকেজ
echo "📚 প্রয়োজনীয় প্যাকেজ ইনস্টল হচ্ছে..."
pip install --upgrade pip
pip install -r requirements.txt

# পারমিশন
chmod +x run.sh

echo ""
echo "✅ সেটআপ সম্পন্ন!"
echo ""
echo "📝 আপনার সাইট যোগ করুন:"
echo "   config/websites.py ফাইল এডিট করুন"
echo ""
echo "🚀 চালাতে: ./run.sh"