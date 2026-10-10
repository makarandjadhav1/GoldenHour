"""Generate backend/data/kb.json. Sources are ONLY those verified in BRD 2.1. Run: python tools/make_kb.py"""
import json
A = {"title": "Special Advisory, Cyber Jagrookta Divas (Canara Bank / I4C), April 2023", "publisher": "Canara Bank / I4C",
     "url": "https://canarabank.com/UploadedFiles/Pdf/(57) Special Advisory Cyber Jagrookta Divas-April 2023.pdf"}
N = {"title": "Got scammed online? Here's what you can do", "publisher": "Newschecker",
     "url": "https://newschecker.in/scam-watch/got-scammed-online-heres-what-you-can-do"}
O = {"title": "How to report suspected fraud communication via DoT's Chakshu facility", "publisher": "Outlook Money",
     "url": "https://www.outlookmoney.com/retirement/financial-planning/how-to-report-suspected-fraud-communication-via-dots-chakshu-facility"}
I = {"title": "How India's cyber crime incidence is rising", "publisher": "IndiaSpend",
     "url": "https://www.indiaspend.com/data-viz/dataviz-how-indias-cyber-crime-incidence-is-rising-972933"}
S = {"title": "Indians lose over Rs 52,976 crore to cyber frauds over six years: Report", "publisher": "IANS",
     "url": "https://ianslive.in/indians-lose-over-rs-52976-crore-to-cyber-frauds-over-six-years-report--20260103154943"}
H = {"title": "Cyber fraud complaints: 12.7 lakh in six months (reporting Indian Express)", "publisher": "Anantam IAS",
     "url": "https://anantamias.com/current-affairs/cyber-fraud-complaints-12-7-lakh-six-months/?pdf=1"}
E = {"title": "Cyber fraud complaints cross 12.7 lakh in six months (secondary source)", "publisher": "EaseMyPrep",
     "url": "https://easemyprep.in/news/3062-cyber-fraud-complaints-cross-127-lakh-in-six-months-rs-10178-crore-lost"}

rows = [
 ("what-is-1930", "What is 1930?", "1930 is India's national helpline for cyber financial fraud. It is run by state and Union Territory law enforcement. Call it as early as you can after losing money.",
  ["1930", "helpline", "number", "call"], [A, N]),
 ("what-is-portal", "What is cybercrime.gov.in?", "It is the National Cyber Crime Reporting Portal. Victims can file a complaint there themselves, with or without calling 1930 first.",
  ["portal", "cybercrime.gov.in", "ncrp", "website", "complaint"], [N]),
 ("call-or-portal", "Do I call 1930 or file on the portal?", "Do both. Calling 1930 starts the process quickly, and a formal complaint is then needed on cybercrime.gov.in within 24 hours. You can also file on the portal yourself.",
  ["call", "portal", "both", "which", "1930"], [A, N]),
 ("what-to-keep-ready", "What details should I keep ready for the 1930 call?", "The operator asks for the minimum: your mobile number, bank name, account number or UPI ID, the 12-digit UTR of the transaction, the date, card details if a card was used, and screenshots.",
  ["details", "ready", "documents", "need", "information"], [A]),
 ("what-is-utr", "What is a UTR?", "A UTR (also called UPI Ref No. or RRN) is the 12-digit reference number of a UPI or IMPS transaction. The 1930 operator asks for it.",
  ["utr", "rrn", "reference", "transaction id", "upi ref"], [A]),
 ("where-find-utr", "Where do I find my transaction ID (UTR)?", "Open your bank or UPI app, go to transaction history, and open the payment. It may be called UPI Ref No. or RRN. In Google Pay it appears as the UPI transaction ID. Take a screenshot.",
  ["find", "utr", "where", "transaction id", "history", "google pay"], [A]),
 ("cant-find-utr", "What if I can't find the UTR?", "Call 1930 anyway and give what you have: amount, date, time, bank and the scammer's number or UPI ID. Look for the UTR afterwards in your app history or your bank's debit SMS.",
  ["cant", "missing", "lost", "utr", "no transaction id"], [A]),
 ("formal-complaint-24h", "Is a formal complaint needed after I call 1930?", "Yes. After the call, a formal complaint is due on the portal within 24 hours.",
  ["24 hours", "formal", "complaint", "deadline", "after call"], [A]),
 ("reference-sms", "What is the reference number SMS?", "After you call 1930, an SMS arrives with a complaint reference number. Keep it. You use it on the portal and with your bank.",
  ["sms", "reference number", "acknowledgement", "complaint number"], [A]),
 ("chakshu", "What is Chakshu for?", "Chakshu (on Sanchar Saathi) is for reporting suspected fraud calls, SMS and messages. It is not for money you have already lost. For a loss, call 1930 and use the portal.",
  ["chakshu", "sanchar saathi", "suspected", "report message"], [O]),
 ("digital-arrest-legal", "Is 'digital arrest' real?", "No. There is no concept of 'digital arrest' in Indian law. Police or agencies do not arrest people over a video call or ask for money to clear a case.",
  ["digital arrest", "video call", "police", "arrest", "cbi"], [I]),
 ("who-asks-otp", "What does the 1930 agent ask me? Will they ask for my OTP?", "The details the agent asks for are listed in the official advisory: mobile, bank, account or UPI ID, UTR, date, card details if used, and screenshots. OTP, PIN, CVV and passwords are not on that list. Never share them with anyone.",
  ["otp", "pin", "cvv", "password", "agent", "fake helpline"], [A]),
 ("evidence-to-keep", "What evidence should I keep?", "Screenshots of the transactions, the scammer's number and messages. The advisory lists screenshots among the things to have when you report.",
  ["evidence", "screenshot", "proof", "keep"], [A]),
 ("how-big-is-problem", "How common is cyber fraud in India?", "In 2025, about 21.8 lakh cheating complaints were reported, with losses of about ₹19,813 crore (IANS, January 2026). You are not alone.",
  ["how common", "statistics", "numbers", "alone", "2025"], [S]),
 ("investment-scams", "Which scams cause the most loss?", "Investment schemes caused about 77% of the losses in 2025, and 'digital arrest' scams about 8% (IANS, January 2026).",
  ["investment", "most common", "trading", "loss", "stock"], [S]),
 ("first-half-2026", "What do the latest numbers say?", "From 1 January to 30 June 2026, about 12.71 lakh complaints were filed and over ₹10,178.97 crore was lost.",
  ["2026", "latest", "recent", "six months"], [H, E]),
 ("money-frozen-refunded", "How much money is recovered?", "Between 2021 and May 2026, about ₹64,447 crore was lost, ₹10,718 crore frozen and ₹323 crore refunded (secondary source). Reporting early improves the chance of freezing money, but nobody can promise a refund.",
  ["refund", "recover", "frozen", "get money back", "chances"], [E]),
]
kb = [dict(id=i, q={"en": q}, a={"en": a}, keywords=k, sources=s, verifiedOn="2026-10-10", reviewBy="2027-01-10") for i, q, a, k, s in rows]
json.dump(kb, open("backend/data/kb.json", "w"), indent=1, ensure_ascii=False)
print(len(kb))
