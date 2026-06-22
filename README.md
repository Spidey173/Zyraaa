# 🔮 ZYRA: Next-Generation Social Experience

<p align="center">
  <img src="https://img.shields.io/badge/Django-5.2.4-092E20?style=for-the-badge&logo=django&logoColor=white" alt="Django" />
  <img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/Database-PostgreSQL%20%2F%20SQLite-4169E1?style=for-the-badge&logo=postgresql&logoColor=white" alt="Database" />
  <img src="https://img.shields.io/badge/Cloud%20Media-Cloudinary-3448C5?style=for-the-badge&logo=cloudinary&logoColor=white" alt="Cloudinary" />
  <img src="https://img.shields.io/badge/Server-Daphne-FF6600?style=for-the-badge&logo=fastapi&logoColor=white" alt="Daphne" />
</p>

<p align="center">
  <b>Zyra</b> is an ultra-modern, visually stunning social platform inspired by Instagram. Engineered with a robust <b>Django 5.2</b> architecture and a custom <b>glassmorphic dark UI</b>, Zyra delivers a premium, highly interactive user experience.
</p>

---

## 🗺️ System Architecture

```mermaid
graph TD
    %% Styling Definitions
    classDef client fill:#4285F4,stroke:#333,stroke-width:2px,color:#fff;
    classDef gateway fill:#FF6600,stroke:#333,stroke-width:2px,color:#fff;
    classDef app fill:#092E20,stroke:#333,stroke-width:2px,color:#fff;
    classDef storage fill:#3448C5,stroke:#333,stroke-width:2px,color:#fff;
    classDef local fill:#7b2cbf,stroke:#333,stroke-width:2px,color:#fff;

    Client["🌐 Client Browser (HTML5 / Custom CSS / JS)"]:::client
    Daphne["⚡ Daphne ASGI Gateway Server"]:::gateway
    Django["🦄 Django Core (App Logic / Views / Context)"]:::app
    DB[("💾 PostgreSQL (Neon) / SQLite")]:::storage
    Cloudinary["☁️ Cloudinary Storage (CDN Assets)"]:::storage
    StaticFiles["📂 WhiteNoise Compressed Static Cache"]:::local

    Client -->|HTTPS Requests| Daphne
    Daphne -->|Routing / Middleware| Django
    Django -->|Reads/Writes Data| DB
    Django -->|Serves CSS/Assets| StaticFiles
    Django -->|Syncs/Retrieves Media| Cloudinary
```

---

## ✨ Features Showcase

### 📱 Core Capabilities

<table>
  <tr>
    <td width="50%">
      <h4>👤 Identity & Profiles</h4>
      <ul>
        <li>Secure user registration, authentication, and session control.</li>
        <li>Fully customizable profile hubs with avatars, bio cards, and status tags.</li>
        <li>Real-time follower and following counters.</li>
      </ul>
    </td>
    <td width="50%">
      <h4>📸 High-Fidelity Media Feeds</h4>
      <ul>
        <li>Advanced media support for both crisp photos and dynamic video posts.</li>
        <li>On-the-fly image optimization and CDN caching powered by Cloudinary.</li>
        <li>Chronological home feeds and randomized exploration grid discovery.</li>
      </ul>
    </td>
  </tr>
  <tr>
    <td width="50%">
      <h4>💬 Engagement Loop</h4>
      <ul>
        <li>Instantly like and unlike posts with reactive micro-animations.</li>
        <li>Interactive comment threads integrated directly inside posts.</li>
        <li>Toggleable bookmarks to curate collections of your favorite posts.</li>
      </ul>
    </td>
    <td width="50%">
      <h4>🔔 Activity Hub</h4>
      <ul>
        <li>Comprehensive notification center keeping you updated on likes, comments, and new followers.</li>
        <li>Real-time visual badges for unread actions and events.</li>
      </ul>
    </td>
  </tr>
</table>

---

## 🎨 Visual Design Philosophy

Zyra utilizes a state-of-the-art **Glassmorphic Dark Theme** to deliver a sleek, premium application interface:
- **Harmonious Palette:** Clean dark slate surfaces combined with vibrant neon violet accents.
- **Micro-Animations:** Fluid transitions on hover, click, and interaction states.
- **Glassmorphism:** CSS backdrop-filter techniques providing contextual depth and layout layering.
- **Responsive Layout:** Adaptive grids designed to scale seamlessly across mobile devices, tablets, and desktop displays.

---

## ⚙️ Local Development Setup

Follow this step-by-step setup to launch Zyra on your local machine:

### 1. Prerequisites
Ensure you have the following installed:
*   [Python 3.10+](https://www.python.org/downloads/)
*   [Virtualenv](https://virtualenv.pypa.io/en/latest/)

### 2. Initialization & Environment Configuration
```bash
# Clone the repository
git clone <repository-url>
cd Zyra

# Initialize virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure the Environment
Create a `.env` file in the root directory to store your environment keys:
```env
SECRET_KEY=django-insecure-prod-key-goes-here
DEBUG=True

# DB falls back automatically to local sqlite if DATABASE_URL is omitted
DATABASE_URL=postgresql://user:password@host:port/dbname

# Cloudinary CDN Integration
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret
```

### 4. Run Migrations & Start Server
```bash
# Prepare & update the schema
python manage.py makemigrations
python manage.py migrate

# Run the Django development server
python manage.py runserver
```
Navigate to `http://127.0.0.1:8000` to interact with the platform.

### 5. Bulk Upload Initial Media (Optional)
If you have mock media files in your local `/media` folder, easily sync them to your Cloudinary cloud with our automated helper utility:
```bash
python upload_media.py
```

---

## 🔧 Core Environment Variable Reference

| Variable Name | Required | Default Value | Description |
| :--- | :---: | :--- | :--- |
| `SECRET_KEY` | ⚠️ No | Insecure dev fallback | Secret key for session encryption and csrf tokens. |
| `DEBUG` | ⚠️ No | `True` | Set to `False` in production pipelines. |
| `DATABASE_URL` | ⚠️ No | `sqlite:///db.sqlite3` | Database URI configuration. Supports Neon DB / Postgres. |
| `CLOUDINARY_CLOUD_NAME`| ✅ Yes | — | Cloud name locator for media assets. |
| `CLOUDINARY_API_KEY` | ✅ Yes | — | Cloudinary API Key. |
| `CLOUDINARY_API_SECRET` | ✅ Yes | — | Cloudinary API Secret key. |

---

## 🚢 Production Deployment

Zyra is fully optimized for containerless deployment (e.g., Heroku, Render, Railway). 

*   **Static Assets:** Handled by **WhiteNoise** with Gzip compression and browser caching policies.
*   **Gateway Interface:** Utilizes **Daphne** as the ASGI app server to support standard HTTP and asynchronous capabilities:
    ```text
    web: daphne -b 0.0.0.0 -p $PORT config.asgi:application
    ```

---

## 📄 License
Distributed under the MIT License. See [LICENSE](LICENSE) for details.
