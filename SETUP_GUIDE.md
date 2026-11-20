# 24/7 Autonomous AI Agent - Setup & Cloud Activation Guide

This document explains step-by-step how to activate the autonomous AI agent so that it **runs 24/7 in GitHub's cloud without needing your laptop turned on or Antigravity open**.

---

## Nepali Guide (नेपालीमा निर्देशन)

### Setup गर्न आवश्यक कुराहरू (Requirements):

| Requirement | Purpose | कसरी लिने (How to get) |
| :--- | :--- | :--- |
| **GitHub Actions** | Daily cloud execution (ल्यापटप बन्द हुँदा पनि चल्ने) | GitHub मा repo push गर्नासाथ उपलब्ध हुन्छ |
| **AI API Key** | AI ले कोड analyze र safe improvements गर्न | [Google AI Studio](https://aistudio.google.com/) बाट नि:शुल्क (Free) Gemini API Key लिने |
| **GitHub Repo Access** | Cloud बाट commit तथा push गर्न | Repository Settings मा "Read and write permissions" enable गर्ने |
| **Scheduled Workflow** | प्रत्येक दिन automatically run भएर 4 meaningful commit गर्न | `.github/workflows/autonomous-dev-agent.yml` पहिले नै तयार छ |

---

## Step-by-Step Setup Instructions

### चरण १: नयाँ GitHub Repository सिर्जना गरी Code Push गर्ने (Create Repo & Push)

1. [GitHub.com](https://github.com/) मा जानुहोस् र नयाँ Repository सिर्जना गर्नुहोस् (उदा: `devpulse-ai` वा `ai-contribution-agent`)।
2. आफ्नो कम्प्युटरको टर्मिनलमा यो कमाण्डहरू चलाउनुहोस्:

```bash
cd "c:\Users\VICTUS\Desktop\ai automation"

# Remote GitHub URL थप्नुहोस् (तपाईंको GitHub username र repo name हाल्नुहोस्)
git remote add origin https://github.com/<YOUR_GITHUB_USERNAME>/<YOUR_REPO_NAME>.git

# Initial commit र push गर्नुहोस्
git add .
git commit -m "feat: initial commit of DevPulse application and 24/7 autonomous AI agent"
git branch -M main
git push -u origin main
```

---

### चरण २: GitHub Actions Workflow Permissions Enable गर्ने (Crucial!)

GitHub Actions लाई तपाईंको repo मा commit र push गर्ने permission दिनु पर्छ:

1. GitHub मा आफ्नो repository खोल्नुहोस्।
2. माथिको **Settings** ट्याबमा थिच्नुहोस्।
3. बायाँ साइडबारमा **Actions** -> **General** मा क्लिक गर्नुहोस्।
4. तल स्क्रोल गरी **Workflow permissions** सेक्सनमा जानुहोस्:
   - **Read and write permissions** चयन गर्नुहोस्।
   - **"Allow GitHub Actions to create and approve pull requests"** चेकबक्समा टिक लगाउनुहोस्।
5. **Save** मा थिच्नुहोस्।

---

### चरण ३: Gemini AI API Key थप्ने (Add Gemini Secret)

AI लाई smart code improvements गराउन Gemini API Key थप्नुहोस्:

1. [Google AI Studio](https://aistudio.google.com/) मा जानुहोस् र नि:शुल्क (Free) API Key प्राप्त गर्नुहोस् (Get API Key थिच्नुहोस्)।
2. GitHub मा आफ्नो Repository को **Settings** -> **Secrets and variables** -> **Actions** मा जानुहोस्।
3. **New repository secret** हरियो बटनमा थिच्नुहोस्।
4. भर्नुहोस्:
   - **Name:** `GEMINI_API_KEY`
   - **Secret:** तपाईंको Gemini API Key पेस्ट गर्नुहोस् (उदा: `AIzaSy...`)
5. **Add secret** मा थिच्नुहोस्।

*(वैकल्पिक: यदि तपाईंसँग OpenAI Key छ भने `OPENAI_API_KEY` पनि त्यसरी नै थप्न सक्नुहुन्छ)*

---

### चरण ४: पहिलो पटक म्यानुअल रूपमा जाँच्ने (Test Immediately)

तपाईंले तुरुन्तै जाँच्न सक्नुहुन्छ कि यसले कसरी काम गर्छ:

1. GitHub मा **Actions** ट्याबमा जानुहोस्।
2. बायाँ तर्फ **"24/7 Autonomous AI Contribution Agent"** workflow मा थिच्नुहोस्।
3. दायाँ छेउमा **Run workflow** बटन देखिनेछ:
   - Target commits: `4`
   - Model: `gemini-2.5-flash`
4. **Run workflow** थिच्नुहोस्।
5. २-३ मिनेटमा यो सम्पन्न हुनेछ र तपाईंको repository मा ४ वटा नयाँ meaningful commit आउनेछन् साथै `reports/daily/` फोल्डरमा activity report बन्नेछ।

---

### चरण ५: ल्यापटप बन्द गर्नुहोस्! (Turn Off Laptop)

- अब तपाईंले आफ्नो ल्यापटप बन्द गर्न सक्नुहुन्छ, इन्टरनेट विच्छेद गर्न सक्नुहुन्छ, र Antigravity पूर्ण रूपमा बन्द गर्न सक्नुहुन्छ।
- GitHub को Cloud Server ले दैनिक **०२:०० UTC** मा आफैঁ wake up भएर:
  1. कोड fetch गर्छ।
  2. टेस्टहरू चलाउँछ।
  3. सुधारहरू पहिचान गर्छ।
  4. कोड परिवर्तन गर्छ।
  5. टेस्ट पास भए मात्र commit गर्छ।
  6. Repository मा push गर्छ।
  7. अर्को दिन सम्म सुरक्षित विश्राम गर्छ।

---

## शेड्युल परिवर्तन गर्ने तरिका (Customize Daily Schedule)

`.github/workflows/autonomous-dev-agent.yml` फाइल खोलेर cron समय परिवर्तन गर्न सक्नुहुन्छ:

- **दिनको १ पटक (02:00 UTC):**
  ```yaml
  - cron: '0 2 * * *'
  ```
- **दिनको २ पटक (बिहान र बेलुका):**
  ```yaml
  - cron: '0 2,14 * * *'
  ```
- **दिनको ४ पटक (हरेक ६ घण्टामा १-१ commit):**
  ```yaml
  - cron: '0 3,9,15,21 * * *'
  ```

---

## परियोजना सुरक्षा नियमहरू (Strict Safeguards)

एजेन्टले यी नियमहरूको कडा पालना गर्छ:
1. **Never Delete Project**: कुनै पनि अवस्थित फाइल वा फोल्डर मेट्दैन।
2. **Never Break Tests**: कोड सुधार गरेपछि यदि एउटा पनि unit test fail भयो भने त्यो परिवर्तन तत्काल **rollback** गर्छ।
3. **No Fake Commits**: खाली commit वा fake commit कहिल्यै गर्दैन।
4. **No Secret Leaks**: `.env`, credentials, वा API keys लाई कहिल्यै छुँदैन वा commit गर्दैन।
5. **Pre-Commit Safety Backup**: कुनै पनि काम सुरु गर्नु अघि local backup branch बनाउँछ।
