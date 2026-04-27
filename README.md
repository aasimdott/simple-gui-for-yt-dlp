# simple-gui-for-yt-dlp
frontend of yt-dlp for command less downloads


yt-dlp GUI (Linux Binary)
A lightweight, standalone graphical user interface for the powerful yt-dlp engine. This tool allows users on Debian-based distributions to download high-quality video and audio from thousands of websites without using the command line.
✨ Key Features

    Tor Proxy Support: Built-in option to route your traffic through the Tor network for enhanced privacy and to bypass geo-restrictions (requires a running Tor Browser or service).
    Custom Download Folder: Integrated folder selector to choose exactly where your files are saved.
    Standalone Binary: No need to manage Python environments or dependencies; simply download and run.
    Debian Optimized: Designed to work seamlessly on Ubuntu, Linux Mint, and other Debian-based distros.

🚀 Quick Start (Debian/Ubuntu)
1. Requirements
Ensure you have ffmpeg installed to allow for merging high-quality video and audio streams:
bash

sudo apt update && sudo apt install yt-dlp tor ffmpeg 

2. Installation

    Download the latest UDM.Universal.Download.Module binary from the Releases page.
    Navigate to your downloads folder and make the binary executable:
    bash

    chmod +x UDM.Universal.Download.Module

3. Usage
Double-click the binary or run it via terminal:
bash

./UDM.Universal.Download.Module

⚙️ Configuration & Features
📂 Download Folder Selection
By default, files are saved to your current directory. Click the "Select Folder" button within the GUI to set a custom destination path for your downloads.
🧅 Using the Tor Proxy (Optional)
To use the Tor proxy feature:

    Open the Tor Browser or start the Tor service (sudo systemctl start tor).
    Check the "Enable Tor Proxy" box in the GUI.
    The application will automatically route requests through socks5://127.0.0.1:9050 (or 9150 for Tor Browser).

🛠 Troubleshooting

    Binary won't launch: Ensure you have granted execution permissions (chmod +x).
    Download fails: Check if your version of yt-dlp is up to date. This GUI often bundles its own, but you can manually update the core by running yt-dlp -U if you have it installed globally.
    
    (Optional)Tor Errors: Ensure Tor is actually running on your system before enabling the proxy option.
