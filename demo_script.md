# VoiceOps 2026: 2-Minute Spoken Support Agent Demo Script

This script walks through the three required judging criteria in under 2 minutes:
1. **Document-Grounded Question Answering** (with strict policy adherence).
2. **Context-Aware Follow-Up** (coreference resolution without repeating parameters).
3. **Graceful Refusal / Human Handover** or **"I don't know" for unsupported queries**.

---

## Act 1: Document QA & Grounded Policy (0:00 - 0:40)

- **Customer (Audio In):**
  > *"Hello, mujhe order ke baare mein help chahiye."*
- **Agent (Voice Out - Kaveri):**
  > *"Hello! Main ZentroMart ka AI support assistant hoon. Main aapki kaise madad kar sakta hoon? Please apna order number share karein."*
- **Customer (Audio In):**
  > *"Order number hai 8978 2837."*
- **Agent (Voice Out - Kaveri):**
  > *"Order details verify karne ke liye, please registered phone number ke last four digits ya delivery pincode share karein."*
- **Customer (Audio In):**
  > *"Last four digits 4533 hain."*
- **Agent (Voice Out - Kaveri):**
  > *"Thank you, verification complete ho gaya hai. Main aapke order 8 9 7 8 2 8 3 7 ke baare mein kaise help kar sakta hoon?"*

---

## Act 2: Contextual Follow-Up & Order Coreference (0:40 - 1:15)

- **Customer (Audio In):**
  > *"Mera order shipped hai, delivery kab tak hogi?"*
- **Agent (Voice Out - Kaveri):**
  > *"Aapka order ship ho chuka hai aur 22 October 2026 tak delivery schedule hai."*
- **Customer (Audio In):**
  > *"Aur agar main delivery ke time ghar par na miloon to kya hoga?"* *(Follow-up testing coreference & DEL-3)*
- **Agent (Voice Out - Kaveri):**
  > *"Agar aap ghar par nahi hain, to courier 3 delivery attempts karega, jiske baad parcel warehouse return ho jaata hai."*

---

## Act 3: Policy Refusal & Human Handover / "I Don't Know" (1:15 - 2:00)

### Variation A: Human Escalation for High-Value Damage (Policy DWM-3 & ESC-1)
- **Customer (Audio In):**
  > *"Maine TV damage report kiya tha. Aap abhi replacement approve kar do na?"*
- **Agent (Voice Out - Kaveri):**
  > *"Ye high-value item above ten thousand rupees hai, isliye policy ke mutabik AI ise direct approve nahi kar sakta. Maine Priority Resolution team ke liye ticket create kar diya hai aur ek specialist colleague aapse jald rabta karenge."*

### Variation B: Unsupported Inquiry ("I don't know")
- **Customer (Audio In):**
  > *"Kya main midnight delivery schedule kar sakta hoon?"*
- **Agent (Voice Out - Kaveri):**
  > *"Sorry, iske baare mein mere paas internal documents mein jaankari nahi hai. Main aapko ek human colleague se connect kar sakti hoon."*

---

## Technical Highlights Demonstrated
- **Speech-to-Text**: Gnani STT REST/WebSocket (`en-IN` handling mixed Hindi-English speech).
- **Security & Privacy**: Zero order details leaked prior to phone/pincode verification (`lookup_order`).
- **Grounded RAG**: Exact citation of policy sections (`STY-1`, `IDV-2`, `DEL-3`, `DWM-3`, `ESC-1`).
- **Text Normalization for the Ear**: Spoken dates ("the 22nd of October 2026") and spaced order IDs ("8 9 7 8 2 8 3 7").
- **Voice Synthesis**: Gnani TTS model `timbre-v2.5` with voice `Kaveri`.
