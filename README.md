# ScribingAgent

An AI-powered medical documentation and coding assistant that leverages OpenAI, Azure Cognitive Search, and Firebase to streamline medical scribing processes.

## Overview

ScribingAgent is a Python-based application designed to assist with medical documentation and coding tasks. It combines modern AI capabilities with cloud services to provide intelligent medical information processing and documentation support.

## Features

- **AI-Powered Medical Documentation**: Utilizes OpenAI and LangChain for intelligent text processing
- **Azure Cognitive Search Integration**: Enables powerful search capabilities across medical data
- **Firebase Backend**: Provides real-time data storage and authentication
- **Streamlit Interface**: User-friendly web interface for easy interaction
- **Medical Coding Support**: Specialized tools for medical coding workflows

## Tech Stack

- **Language**: Python
- **AI/ML**: OpenAI API, LangChain (v0.0.272)
- **Cloud Services**: 
  - Azure Cognitive Search (v11.4.0b8)
  - Firebase Admin SDK
- **Frontend**: Streamlit
- **Data Processing**: Pandas
- **PDF Generation**: WeasyPrint

## Installation

1. Clone the repository:
```bash
git clone https://github.com/shivamd1810/scribingAgent.git
cd scribingAgent
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
Create a `.env` file in the root directory and add your API keys:
```env
OPENAI_API_KEY=your_openai_api_key
AZURE_SEARCH_ENDPOINT=your_azure_endpoint
AZURE_SEARCH_KEY=your_azure_key
# Add other required environment variables
```

4. Configure Firebase:
- Place your Firebase service account credentials in the appropriate location
- Update `firebase.json` with your project configuration

## Usage

Run the application:
```bash
streamlit run app.py
```

The application will start on `http://localhost:8501` by default.

## Project Structure

```
scribingAgent/
├── app.py                    # Main application entry point
├── azureCognitiveSearch.py   # Azure search functionality
├── firebaseFunctions.py      # Firebase operations
├── prompt.py                 # AI prompt management
├── tools.py                  # Utility functions
├── medicalCoding/           # Medical coding specific modules
├── requirements.txt         # Python dependencies
├── firebase.json           # Firebase configuration
└── README.md              # This file
```

## Key Components

- **app.py**: Main Streamlit application that provides the user interface
- **azureCognitiveSearch.py**: Handles integration with Azure Cognitive Search for medical data retrieval
- **firebaseFunctions.py**: Manages Firebase operations including data storage and retrieval
- **prompt.py**: Contains prompt engineering logic for AI interactions
- **tools.py**: Utility functions and helper methods

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request


