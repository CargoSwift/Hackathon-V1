# 🚀 Space Cargo Management System  

## 📌 Project Overview  
The **Space Cargo Management System** is designed to help astronauts **efficiently store, retrieve, and manage cargo** on the **International Space Station (ISS)**.  
It ensures **optimized storage, quick retrieval, waste tracking, and cargo return planning** while being efficient in computational resource usage.  

## 🎯 Core Features  
✅ **Cargo Placement Optimization** – Suggests **best storage locations** for new items based on priority & space availability.  
✅ **Fast Retrieval System** – Finds **easily accessible** items with minimal movement required.  
✅ **Rearrangement Suggestions** – Optimizes storage when space is running low.  
✅ **Waste Management & Return Planning** – Automatically **marks expired/depleted items** and suggests **return plans**.  
✅ **Time Simulation** – Allows astronauts to **fast forward time** and analyze cargo usage over days.  
✅ **Logging & API-based System** – Keeps track of **every action (placement, retrieval, disposal, etc.)**.  
✅ **Fully Dockerized Deployment** – Ensures the system is **portable and scalable**.  

---

## 👨‍💻 Team Members & Assigned Roles  

### **1️⃣ Backend Developer – Jigme**  
🛠️ **Responsibilities:**  
- Develop the **backend APIs** for item placement, retrieval, waste management, and time simulation.  
- Implement **database models** and ensure **data consistency**.  
- Optimize **retrieval & placement algorithms** for better performance.  
- Ensure API endpoints work **efficiently and securely**.  

🚀 **Tech Stack:** Python (FastAPI), PostgreSQL, Docker.  
📂 **Main Folder:** `/backend`  

---

### **2️⃣ Data & Simulation Engineer – Vaibhav**  
🛠️ **Responsibilities:**  
- Write **placement & retrieval optimization algorithms**.  
- Implement **time simulation logic** for tracking cargo usage & expiry.  
- Ensure efficient **priority-based item placement & retrieval**.  
- Optimize system for **handling thousands of items with minimal compute power**.  

🚀 **Tech Stack:** Python (NumPy, Pandas), Optimization Libraries, API Integration.  
📂 **Main Folder:** `/data-processing`  

---

### **3️⃣ DevOps & Integration Engineer – Rishita**  
🛠️ **Responsibilities:**  
- Ensure **seamless integration** of backend, frontend, and data logic.  
- Set up **Dockerized deployment** (Dockerfile & containerization).  
- Implement **CI/CD pipeline** for continuous integration.  
- Automate **testing & debugging** for smooth deployment.  

🚀 **Tech Stack:** Docker, GitHub Actions, Postman for API Testing.  
📂 **Main Folder:** `/devops`  

---

### **4️⃣ Frontend Developer – Adithya**  
🛠️ **Responsibilities:**  
- Develop a **user-friendly dashboard** for astronauts.  
- Build pages for **cargo placement, retrieval, and waste tracking**.  
- Ensure **real-time inventory visualization**.  
- Integrate APIs and provide a clean **UI/UX experience**.  

🚀 **Tech Stack:** React.js, Tailwind CSS, API Integration (Fetch/Axios).  
📂 **Main Folder:** `/frontend`  

---

## 📦 Tech Stack Used  
| Component    | Technology Stack         |
|-------------|--------------------------|
| **Backend**  | FastAPI, PostgreSQL|
| **Frontend** | React.js, Tailwind CSS   |
| **Data Processing** | Python, NumPy, Pandas |
| **Deployment** | Docker, GitHub Actions |

---

## 🔧 Installation & Setup  

### **Clone the Repository**
```bash
git clone https://github.com/CargoSwift/Hackathon-V1.git
cd Hackathon-V1

### **Setup Backend (Jigme)**
cd backend
python -m venv venv
pip install -r requirements.txt  # Python dependencies
python server.py  # Start FastAPI server

### **Setup Frontend (Adithya)**
cd frontend
npm install
npm start  # Run React.js frontend



### **Setup Docker Deployment**

docker build -t space-cargo .
docker run -d -p 5173:5173 -p 8000:8000 -p 5432:5432 -v pg_data:/var/lib/postgresql/data --name fullstack-container space-cargo
