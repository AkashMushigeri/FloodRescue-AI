# FloodRescue AI — 3-Minute Video Demo Script

**Hackathon Track:** Heat and Water — WeMakeDevs × AWS Environmental Hackathon 2026  
**Target Video Duration:** 2 minutes 50 seconds (strictly under 3:00)  
**Presenter Tone:** Professional, empathetic, technically grounded.

---

### **0:00 – 0:25 | Scene 1: The Disaster Reality (Problem Context)**
- **Screen:** Show FloodRescue AI landing page banner.
- **Voiceover:**
  > "During flash floods and urban inundations, emergency helplines are instantly overwhelmed. Citizens send fragmented distress calls across WhatsApp, SMS, and phone lines. Meanwhile, rescue coordinators lack a unified map of where people are trapped, who is in immediate danger of drowning, and where specialized boat units should be dispatched.
  > This is **FloodRescue AI**: Every Distress Signal Matters, Every Rescue Counts."

---

### **0:25 – 1:00 | Scene 2: Survivor SOS Submission (`/help`)**
- **Screen:** Navigate to `/help`. Fill out live distress form.
  - People: `4`
  - Name: `Meera Sundaram`
  - Contact: `+91 98401 23456`
  - Water Level: Click **Chest Deep**
  - Injuries: Toggle **Yes** → `Elderly grandmother with asthma, inhaler running low`
  - Special Needs: Check `Elderly`, `Children`, `Medical Devices`
  - Landmark: `14, 2nd Cross St, Gandhi Nagar, Adyar`
  - Geolocation: Click `Use My GPS Location` or pin on map.
  - Distress Message: *"Water entering ground floor rapidly. Electricity cut. Trapped with 82yo asthma patient and two children. Need boat evacuation urgently."*
- **Action:** Click **TRANSMIT RESCUE SOS**.
- **Screen:** Immediate confirmation card with unique incident ID `INC-2026-XXXX`.
- **Voiceover:**
  > "A survivor in crisis can report their emergency in seconds without creating an account or remembering passwords. Notice that even if GPS is degraded indoors or in torrential rain, approximate landmarks are first-class citizens. The incident is securely persisted in the backend before any AI processing begins."

---

### **1:00 – 1:35 | Scene 3: Strands AI Agent Triage & Explainability**
- **Screen:** Scroll down on the tracking view and open the Operations Center `/responder`.
  - Highlight the AI Triage Card for the newly submitted incident.
  - Highlight Priority: `CRITICAL` badge.
  - Show the explainable reasons:
    - *Chest-deep rising water*
    - *Asthma patient with diminishing oxygen supply*
    - *2 trapped minors without electricity*
- **Voiceover:**
  > "Here is our AI Agent at work, built using the AWS Strands Agents SDK and Amazon Bedrock. Rather than treating AI as a black box or hallucinating probabilities, our agent extracts structured indicators from unstructured text and executes deterministic safety rules. It clearly shows the operational commander *why* this report was flagged as Critical, and alerts them to missing details like building floor level."

---

### **1:35 – 2:15 | Scene 4: Operations Command & Fleet Dispatch (`/responder`)**
- **Screen:** Show the Operations Center:
  - Metrics cards: Highlight the strict distinction between **People Reported** (sum of humans) vs **Known Incidents**.
  - Interactive Leaflet map: Click the red pulse marker on Adyar.
  - Click **Acknowledge Report** → Status becomes `ACKNOWLEDGED`.
  - In Team Assignment dropdown, select **Swift Water Rescue Unit 1 (Boat Squad)**.
  - Click **Authorize & Dispatch Unit**.
  - Switch tab to `/teams`: Show Swift Water Unit status updated to `DISPATCHED`.
  - Switch back to Survivor tracking tab: Show the survivor's screen updated live to `ASSIGNED: Swift Water Rescue Unit 1`.
- **Voiceover:**
  > "The operations dashboard gives multi-agency commanders complete situational awareness. Notice that we never claim to count unregistered cellular phones—we strictly report verified citizen reports. The commander acknowledges the incident and dispatches our specialized Swift Water Boat Squad. Instantly, both the field team's roster and the survivor's tracking view are synchronized in real time."

---

### **2:15 – 3:00 | Scene 5: AWS Serverless Architecture & Honest Boundaries**
- **Screen:** Display `ARCHITECTURE.md` diagram and `infrastructure/template.yaml`.
  - Highlight AWS Serverless stack: API Gateway HTTP API, AWS Lambda, Amazon DynamoDB, AWS Strands Agents SDK on Bedrock.
  - Highlight fail-safe fallback: If Bedrock is throttled or offline, deterministic triage rules ensure zero dropped reports.
- **Voiceover:**
  > "Under the hood, FloodRescue AI is built entirely on AWS serverless services: Amazon API Gateway, AWS Lambda, Amazon DynamoDB with single-table global secondary indexes, and the AWS Strands Agents SDK. If Bedrock or cloud connectivity degrades, the system automatically falls back to deterministic rules so life-saving reports are never dropped.
  > FloodRescue AI bridges the gap between distressed citizens and emergency responders—ensuring that every distress signal matters, and every rescue counts. Thank you."
