# 🌱 AI-Powered Farming Biodiversity App

A comprehensive, modern web application that helps farmers increase biodiversity through intelligent crop identification, companion planting recommendations, and a complete plant database management system.

![Farm Biodiversity Assistant](https://img.shields.io/badge/AI-Powered-green) ![Flask](https://img.shields.io/badge/Flask-2.3.3-blue) ![Tailwind CSS](https://img.shields.io/badge/Tailwind-CSS-38B2AC) ![Gemini API](https://img.shields.io/badge/Gemini-API-orange) ![Database](https://img.shields.io/badge/Plant-Database-brightgreen)

## ✨ Features

### 🎯 **Core Functionality**
- 📸 **Image Upload & Camera Integration** - Upload farm images or capture photos directly with drag-and-drop support
- 🤖 **AI Crop Identification** - Powered by Google's Gemini API for accurate plant recognition and analysis
- 🌿 **Smart Companion Plant Recommendations** - Intelligent suggestions combining database lookup with AI insights
- 📊 **Comprehensive Plant Database** - 15+ pre-loaded crops with detailed companion relationships, soil requirements, and harvest timing
- 📖 **Farming Diary** - Complete crop tracking system with entry management, photo uploads, filtering, and progress monitoring
- 🛠️ **Admin Interface** - Complete CRUD operations for plant database management with search, import/export functionality
- 🎯 **Biodiversity Analysis** - Evaluate current farm setup and suggest improvements for ecosystem health
- 📍 **GPS Location Integration** - Precise location detection for climate-aware recommendations and regional optimization

### 🎨 **User Experience**
- 📱 **Mobile-First Design** - Fully responsive with modern animations
- ✨ **Dynamic Animations** - Floating particles, morphing shapes, interactive effects
- 🎭 **Glass Morphism UI** - Modern translucent design with smooth transitions
- 🖱️ **Interactive Elements** - Mouse trails, hover effects, ripple animations
- 📜 **Parallax Scrolling** - Engaging scroll-based animations

### 💾 **Data Management**
- 💾 **Export/Import Database** - Backup and restore plant database with full JSON support
- 📄 **Export Results** - Save AI recommendations and analysis as downloadable JSON files
- 📖 **Diary Data Management** - Comprehensive entry tracking with backup, recovery, and data validation
- 🌍 **Historical Data Integration** - Consider past planting patterns and local farming history
- 🔄 **Real-time Updates** - Changes reflect immediately across the app without page refresh
- 🔍 **Advanced Search** - Find plants instantly with real-time filtering and search

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Google Gemini API Key ([Get one here](https://makersuite.google.com/app/apikey))

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/arstriker/farming-biodiversity.git
   cd farming-biodiversity
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
   - Main App: `http://localhost:5000`
   - Farming Diary: `http://localhost:5000/diary`
   - Admin Panel: `http://localhost:5000/admin`

## 🛠️ Technology Stack

### Backend
- **Flask 2.3.3** - Lightweight Python web framework with RESTful API
- **Google Gemini API** - Advanced AI for image analysis and plant identification
- **Pillow (PIL)** - Image processing and manipulation
- **python-dotenv** - Secure environment variable management
- **JSON Database** - Lightweight, file-based plant database system

### Frontend
- **HTML5** - Semantic markup with accessibility features
- **Tailwind CSS** - Utility-first CSS framework for rapid UI development
- **JavaScript (ES6+)** - Modern JavaScript with async/await, modules, and DOM manipulation
- **Font Awesome** - Comprehensive icon library
- **Inter Font** - Modern, readable typography optimized for screens

### Advanced Features
- **Responsive Design** - Mobile-first approach with breakpoint optimization
- **Glass Morphism UI** - Modern translucent design with backdrop blur effects
- **CSS Animations** - Smooth transitions, hover effects, and loading states
- **Camera API** - Direct photo capture from device camera
- **Drag & Drop API** - Intuitive file upload with visual feedback
- **Local Storage** - Client-side data persistence for user preferences

## 📁 Project Structure

```
farming-biodiversity/
├── app.py                    # Flask application with API routes
├── requirements.txt          # Python dependencies
├── plant_database.json       # Comprehensive plant database
├── diary_data.json          # Farming diary entries database
├── .env                     # Environment variables (create this)
├── .gitignore              # Git ignore rules
├── history.json            # Historical farming data
├── templates/
│   ├── index.html          # Main application interface
│   ├── diary.html          # Farming diary interface
│   └── admin.html          # Database management interface
├── static/
│   ├── css/
│   │   └── diary.css       # Diary-specific styling
│   └── js/
│       ├── app.js          # Main app JavaScript
│       ├── diary.js        # Diary functionality
│       └── admin.js        # Admin interface JavaScript
└── .kiro/
    └── specs/              # Project specifications
```

## 🎯 How It Works

### 📖 **Farming Diary Features**
The integrated farming diary provides comprehensive crop tracking and management:

1. **Entry Creation** - Document daily farming activities with detailed forms
2. **Crop Tracking** - Monitor growth stages from seed to harvest
3. **Photo Documentation** - Upload images to create visual progress records
4. **Activity Logging** - Track watering, fertilizing, pest control, and other activities
5. **Weather Integration** - Record weather conditions affecting crop growth
6. **Search & Filter** - Find specific entries by crop type, growth stage, or date
7. **Data Export** - Export diary data for backup and analysis
8. **Performance Optimization** - Pagination and caching for large datasets

### 🌾 **Main Application Flow**
1. **Upload Image** - Users upload a photo of their farmland or use device camera
2. **AI Analysis** - Gemini API analyzes the image and identifies existing crops
3. **Crop Confirmation** - Users can confirm, edit, or add crops manually
4. **Smart Recommendations** - System provides suggestions using:
   - **Plant Database** - Instant, accurate recommendations from local database
   - **AI Fallback** - Gemini API for enhanced context when needed
   - **Historical Data** - Past planting patterns and local conditions
   - **Companion Benefits** - Pest control, soil improvement, harvest timing
5. **Detailed Results** - Comprehensive recommendations with:
   - Days to maturity
   - Soil compatibility
   - Specific companion benefits
   - Growing requirements
6. **Export Data** - Save results for future reference

### 🛠️ **Admin Interface Features**
1. **Database Management** - Add, edit, delete plants with comprehensive details
2. **Search & Filter** - Find plants quickly with real-time search
3. **Import/Export** - Backup and restore entire database
4. **Form Validation** - Ensure data integrity with comprehensive forms
5. **Real-time Updates** - Changes immediately available in main app

## 🌿 Example Workflows

### 📱 **Main App Usage**
1. Farmer uploads a picture of their tomato garden
2. In the text box, they add: "Sandy soil, full sun exposure"
3. AI identifies "Tomato" from the image
4. Farmer confirms and adds "Pepper" manually
5. System checks plant database and instantly recommends:
   - **Basil** - "Repels aphids and improves flavor. Harvest in 60 days. Thrives in well-draining soil."
   - **Marigold** - "Natural pest deterrent, repels nematodes. Blooms continuously. Excellent companion for Tomato."
6. Farmer views detailed recommendations and saves results

### 🛠️ **Admin Panel Usage**
1. Admin accesses `/admin` interface
2. Searches for "basil" to edit existing plant data
3. Updates companion plants and adds new soil requirements
4. Adds a new plant "Oregano" with complete growing information
5. Exports database for backup before making major changes
6. Changes are immediately available in the main recommendation system

## 🔌 API Endpoints

The application provides a RESTful API for plant database and diary management:

### Plant Management
- `GET /api/plants` - Retrieve all plants
- `GET /api/plants/<id>` - Get specific plant details
- `POST /api/plants` - Add new plant to database
- `PUT /api/plants/<id>` - Update existing plant
- `DELETE /api/plants/<id>` - Remove plant from database
- `POST /api/plants/import` - Import entire database from JSON

### Diary Management
- `GET /api/diary/entries` - Retrieve diary entries with pagination and filtering
- `POST /api/diary/entries` - Create new diary entry
- `GET /api/diary/entries/<id>` - Get specific diary entry
- `PUT /api/diary/entries/<id>` - Update existing diary entry
- `DELETE /api/diary/entries/<id>` - Delete diary entry
- `GET /api/diary/categories` - Get crop categories and growth stages
- `POST /api/diary/upload` - Upload photos for diary entries

### Application Routes
- `GET /` - Main application interface
- `GET /diary` - Farming diary interface
- `GET /admin` - Database management interface
- `POST /analyze` - AI-powered crop identification
- `POST /recommend` - Get companion plant recommendations

## 🛠️ Admin Interface

Access the admin panel at `/admin` to manage your plant database:

### 📊 **Dashboard Features**
- **Visual Plant Cards** - Overview of all plants with key information
- **Real-time Search** - Find plants instantly as you type
- **Responsive Grid** - Adapts to any screen size
- **Loading States** - Smooth loading animations

### ✏️ **Plant Management**
- **Add Plants** - Comprehensive form with all plant details
- **Edit Plants** - Update any plant information
- **Delete Plants** - Remove plants with confirmation dialog
- **Form Validation** - Ensures data integrity

### 💾 **Data Operations**
- **Export Database** - Download complete database as JSON
- **Import Database** - Upload and replace database from file
- **Backup & Restore** - Easy data management
- **Auto-save** - Changes saved immediately to file system

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the root directory:

```env
GEMINI_API_KEY=your_gemini_api_key_here
```

### Plant Database

The app includes a comprehensive `plant_database.json` with detailed information for 15+ common crops:

```json
{
  "plants": {
    "tomato": {
      "name": "Tomato",
      "scientific_name": "Solanum lycopersicum",
      "companion_plants": ["basil", "marigold", "carrots"],
      "soil_requirements": {
        "type": ["loamy", "well-draining"],
        "ph_range": [6.0, 6.8],
        "fertility": "high"
      },
      "harvest_time": {
        "days_to_maturity": 75,
        "season": "summer to fall"
      },
      "benefits_provided": [
        "attracts beneficial insects",
        "provides shade for smaller plants"
      ]
    }
  }
}
```

### Historical Data

Customize `history.json` with your area's specific data:

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

### 🎭 **Visual Effects**
- **Glass Morphism Effects** - Modern translucent design with backdrop blur
- **Floating Particles** - Animated background particles for dynamic feel
- **Morphing Shapes** - Smooth shape transformations using CSS animations
- **Gradient Animations** - Dynamic background color transitions
- **Pulse Rings** - Expanding ring animations around key elements
- **Text Shimmer** - Animated gradient text effects

### 🖱️ **Interactive Elements**
- **Mouse Trail** - Glowing particles follow cursor movement
- **Ripple Effects** - Click animations on all interactive buttons
- **Hover Transformations** - Smooth scale and glow effects
- **Parallax Scrolling** - Elements move at different speeds when scrolling
- **Touch Interactions** - Mobile-optimized touch feedback
- **Typewriter Effect** - Animated text typing for subtitles

### 📱 **Responsive Design**
- **Mobile-First Approach** - Optimized for all device sizes
- **Adaptive Layouts** - Grid systems that adjust to screen size
- **Touch-Friendly** - Large touch targets and gesture support
- **Loading Animations** - Beautiful loading states with spinners
- **Error Handling** - User-friendly error messages with animations
- **Smooth Scrolling** - Enhanced user experience with scroll animations

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