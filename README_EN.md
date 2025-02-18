# 🇺🇸 US Visa Appointment Rescheduler - Colombia  

This project is an automated bot designed to reschedule U.S. visa appointments on [usvisa-info.com](https://usvisa-info.com). It allows you to **reschedule both the consular and CAS appointments** to a more convenient date and time.  

## 📌 Prerequisites  
- You must already have a **scheduled U.S. visa appointment**.  
- [Optional] An **API Token** from **Pushover** and/or **SendGrid** to receive notifications.  
  - You can also use the **esender.php** file in this repository to send email notifications from your website.  

## ⚠️ Important Information  
- This bot is **adapted for Colombia** and has been successfully tested for rescheduling appointments as of **February 2025**.  
- To use it in other countries, modify the list of supported embassies in the **embassy.py** file.  

### ➕ Adding a New Embassy  
To add an embassy, you need to find its **"facility id"** by following these steps:  

1. In **Google Chrome**, go to the appointment booking page in your account.  
2. **Right-click** on the location section and select **"Inspect"**.  
3. A window will open with the HTML code, highlighting a `<select>` element.  
4. Find the **facility id** and add it to the **embassy.py** file.  
5. If multiple embassies have different **facility ids**, you can add them as well.  

📷 **Example Screenshot:**  
![Finding the Facility ID](https://github.com/Soroosh-N/us_visa_scheduler/blob/main/_img.png?raw=true)  

---

## ⚙️ Initial Setup  
1. **Install dependencies**:  
   - [Google Chrome](https://www.google.com/chrome/)
   - [Python 3](https://www.python.org/downloads/)
   - [ChromeDriver](https://developer.chrome.com/docs/chromedriver/downloads?hl=es-419)

2. **Set up the virtual environment and install dependencies**:  
   - **On Windows**:  
     - Run the `setup.bat` file.  
   - **On Linux**:  
     - Grant execution permissions:  
       ```bash
       chmod +x setup.sh
       ```  
     - Run the script:  
       ```bash
       ./setup.sh
       ```  

   - **Manual Installation** (optional):  
     ```bash
     python3 -m venv venv  
     source venv/bin/activate  # On Windows: venv\Scripts\activate  
     pip install --upgrade pip  # On Windows: python.exe -m pip install --upgrade pip
     pip install -r requirements.txt  
     ```

---

## ▶️ How to Use  
1. Complete the initial setup.  
2. Edit the **config.ini.example** file, save the changes, and rename it to **config.ini**.  
3. [Optional] Configure push notifications in **config.ini**.  
4. [Optional] Modify web notification settings in **config.ini** and **esender.php**.  
5. Run the bot:  
   ```bash
   python3 visa.py
   ```

---

## 🚀 Upcoming Improvements (TODO)  
- Optimize execution timing (**avoid bans and improve performance**).  
- Develop a **Graphical User Interface (GUI)** using **PyQt**.  
- Support **multiple accounts** (switching accounts during rest periods).  
- Improve sound alerts for different events.  
- Expand the list of supported embassies.  

---

## 💙 Acknowledgments  
Special thanks to **@yaojialyu** for the original script and **@uxDaniel, @cejaramillof, and @Soroosh-N** for their contributions and improvements. This project wouldn’t be possible without you! 🚀  

---

### 🌎 **📌 Final Notes**  
This bot was developed to help users in Colombia with the U.S. visa appointment rescheduling process. If you want to adapt it for another country, check the embassy section and make the necessary modifications.  

If you have suggestions or improvements, contributions are welcome! ✨
