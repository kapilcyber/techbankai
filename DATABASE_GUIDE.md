# 🗄️ Database Backup & Environment Guide

This guide provides instructions on how to manage your PostgreSQL database for the TechBank.Ai platform.

> [!IMPORTANT]
> **Fix for "pg_dump is not recognized":** 
> If you get an error that `pg_dump` or `pg_restore` is not recognized, it means the PostgreSQL bin folder is not in your system's PATH. 
> Your PostgreSQL tools are located at: `C:\Program Files\PostgreSQL\16\bin\`

---

## 💾 1. Check Existing Backup File
The system already has a backup file located at:
`backend/techbank.backup`

---

## 📥 2. How to Restore the Database
To import the data from `techbank.backup` into your PostgreSQL database:

### Step A: Create the Database (If not exists)
```sql
-- Open pgAdmin 4 or psql and run:
CREATE DATABASE techbank;
```

### Step B: Run Restore Command
Use the **Full Path** to ensure it works even if your PATH is not set:
```powershell
& "C:\Program Files\PostgreSQL\16\bin\pg_restore.exe" -U postgres -d techbank -v "backend/techbank.backup"
```
*Password is usually `1234` as per your `.env`.*

---

## 📤 3. How to Create a New Dump File
If you want to create a new backup:

```powershell
& "C:\Program Files\PostgreSQL\16\bin\pg_dump.exe" -U postgres -d techbank -Fc > backend/techbank_new.backup
```

---

## 🛠️ 4. How to add to Windows PATH (Optional)
To run these commands without typing the full path every time:
1. Search for **"Edit the system environment variables"** in Windows search.
2. Click **Environment Variables**.
3. Under **System variables**, find **Path** and click **Edit**.
4. Click **New** and paste: `C:\Program Files\PostgreSQL\16\bin`
5. Click **OK** on all windows and **RESTART your terminal**.

---

## ⚙️ 5. Environment (.env) Check
Verify `backend/.env` has:
```env
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=techbank
POSTGRES_USER=postgres
POSTGRES_PASSWORD=1234
```
