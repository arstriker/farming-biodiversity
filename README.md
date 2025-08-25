# 🌱 AI-Powered Farming Biodiversity App

A modern, responsive web application that helps farmers increase biodiversity on their land through AI-powered crop identification and companion planting recommendations.

![Farm Biodiversity Assistant](https://img.shields.io/badge/AI-Powered-green) ![Flask](https://img.shields.io/badge/Flask-2.3.3-blue) ![Tailwind CSS](https://img.shields.io/badge/Tailwind-CSS-38B2AC) ![Gemini API](https://img.shields.io/badge/Gemini-API-orange)

## ✨ Features

- 📸 **Image Upload & Camera Integration** - Upload farm images or capture photos directly
- 🤖 **AI Crop Identification** - Powered by Google's Gemini API for accurate plant recognition
- 🌿 **Companion Plant Recommendations** - Get AI-powered suggestions for sustainable farming
- 📱 **Mobile-First Design** - Fully responsive with modern animations
- 🎨 **Beautiful UI** - Glass morphism effects and smooth animations
- 💾 **Export Results** - Save recommendations as JSON files
- 🌍 **Historical Data Integration** - Consider past planting patterns

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Google Gemini API Key ([Get one here](https://makersuite.google.com/app/apikey))

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/farming-biodiversity-app.git
   cd farming-biodiversity-app
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   # Create .env file and add your Gemini API key
   echo "GEMINI_API_KEY=your_api_key_here" > .env
   ```

5. **Run the application**
   ```bash
   python app.py
   ```

6. **Open your browser**
   Navigate to `http://localhost:5000`

## 🛠️ Technology Stack

### Backend
- **Flask** - Python web framework
- **Google Gemini API** - AI-powered image and text analysis
- **Pillow** - Image processing
- **python-dotenv** - Environment variable management

### Frontend
- **HTML5** - Semantic markup
- **Tailwind CSS** - Utility-first CSS framework
- **JavaScript (ES6+)** - Modern JavaScript features
- **Font Awesome** - Icon library
- **Inter Font** - Modern typography

### Features
- **Responsive Design** - Mobile-first approach
- **Glass Morphism** - Modern UI effects
- **Smooth Animations** - CSS and JavaScript animations
- **Camera API** - Direct photo capture
- **Drag & Drop** - File upload interface

## 📁 Project Structure

```
farming-biodiversity-app/
├── app.py                 # Flask application
├── requirements.txt       # Python dependencies
├── .env                  # Environment variables (create this)
├── .gitignore           # Git ignore rules
├── history.json         # Historical farming data
├── templates/
│   └── index.html       # Main HTML template
├── static/
│   └── js/
│       └── app.js       # Frontend JavaScript
└── .kiro/
    └── specs/           # Project specifications
```

## 🎯 How It Works

1. **Upload Image** - Users upload a photo of their farmland or use device camera
2. **AI Analysis** - Gemini API analyzes the image and identifies existing crops
3. **Crop Confirmation** - Users can confirm, edit, or add crops manually
4. **Get Recommendations** - AI provides companion planting suggestions based on:
   - Current crops
   - Historical planting data
   - Companion planting principles
   - Soil health considerations
5. **View Results** - Detailed recommendations with explanations
6. **Export Data** - Save results for future reference

## 🌿 Example Workflow

1. Farmer uploads a picture of their cornfield
2. In the text box, they add: "I've also seen some clover growing between the rows"
3. AI identifies "Corn" and "Clover"
4. Farmer confirms these are correct
5. App sends confirmed crops + historical data to Gemini API
6. AI suggests "Pole Beans" and "Marigolds" with detailed explanations
7. Farmer views recommendations and saves results

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the root directory:

```env
GEMINI_API_KEY=your_gemini_api_key_here
```

### Historical Data

The app uses `history.json` for historical planting data. You can customize this file with your area's specific data:

```json
{
  "fictional_area_1": {
    "past_seasons": [
      {
        "season": "Spring 2024",
        "crops": ["Corn", "Sunflowers"]
      }
    ],
    "soil_type": "Loamy Sand",
    "notes": "Area is prone to droughts in late summer."
  }
}
```

## 🎨 UI Features

- **Glass Morphism Effects** - Modern translucent design
- **Gradient Animations** - Dynamic background effects
- **Responsive Layout** - Works on all device sizes
- **Touch Interactions** - Mobile-optimized touch feedback
- **Smooth Scrolling** - Enhanced user experience
- **Loading Animations** - Beautiful loading states
- **Error Handling** - User-friendly error messages

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Google Gemini API for AI-powered analysis
- Tailwind CSS for the beautiful styling
- Font Awesome for icons
- Flask community for the excellent framework

## 📞 Support

If you have any questions or need help, please open an issue on GitHub.

---

**Made with 💚 for sustainable farming**