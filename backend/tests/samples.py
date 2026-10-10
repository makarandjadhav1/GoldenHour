"""Synthetic samples. Every name, number, UPI ID and link below is invented."""

MESSAGES = {
    "Fake police video call ('digital arrest')": (
        "Hello, I am Inspector Rakesh Verma from Mumbai Cyber Crime Branch. A parcel booked under your Aadhaar "
        "from FedEx has been seized at customs containing 140 grams of MDMA and 5 fake passports. "
        "You are under digital arrest. Do not disconnect this video call and do not tell anyone, including your family, "
        "or you will be arrested immediately. To verify your innocence, transfer your savings to the RBI safe account "
        "given below within 2 hours. The money will be refunded after verification."
    ),
    "Bank KYC SMS": (
        "Dear customer, your SBI YONO account will be blocked today. Update your PAN/KYC immediately: "
        "http://sbi-kyc-update.top/login and share the OTP you receive to complete verification."
    ),
    "Electricity bill threat": (
        "Dear consumer, your electricity connection will be disconnected tonight 9:30 PM because last month's bill "
        "was not updated. Call our officer 9876543210 immediately and install the MSEB Bill app: "
        "http://mseb-bill-update.xyz/app.apk"
    ),
    "Stock-tip WhatsApp group": (
        "Congratulations! You are selected for our VIP WhatsApp group by SEBI-registered analyst Mr. Arjun Mehta. "
        "Guaranteed 300% returns on IPO allotment, daily profit Rs 8,000. Deposit Rs 10,000 to start: https://bit.ly/3xVIPstock"
    ),
    "Part-time task job": (
        "Hi, I'm Priya from HR. Part-time job: like YouTube videos and earn Rs 4,000 per day. "
        "Pay a Rs 500 registration fee for your prepaid task to withdraw your earnings."
    ),
    "GENUINE bank OTP (should stay low)": (
        "482913 is your OTP for transaction of INR 1,250.00 at AMAZON on your HDFC Bank Card ending 4417. "
        "OTP is valid for 10 minutes. Do not share it with anyone, including bank staff."
    ),
    "GENUINE delivery update (should stay low)": (
        "Your Amazon order #402-1234567-1234567 is out for delivery today. "
        "Track it at https://www.amazon.in/gp/your-account/order-details"
    ),
}

INCIDENTS = {
    "Electricity-bill APK, two UPI debits": (
        "Someone called saying my electricity would be cut tonight and sent an APK called 'MSEB Bill Update' on WhatsApp. "
        "I installed it. Around 4:10 PM today Rs 49,999 was debited from my SBI account XX2234 via UPI, and then "
        "Rs 25,000 at 4:14 PM. UPI Ref No 524587920123 and Ref: 524587920456. The money went to rajesh.kumar77@okaxis. "
        "The caller's number was +91 98765 43210 and the link was http://mseb-bill-update.xyz/app.apk. "
        "My number is 9123456789."
    ),
    "Fake trading group, card + IMPS": (
        "I joined a Telegram stock-tips group and paid into a 'trading platform' on 12/10/2026. "
        "Transaction ID: 612345678901 for Rs 1,20,000 from my HDFC Bank account ending 8841. "
        "They asked me for more to 'unlock withdrawal'. Their website is https://nse-pro-trade.top and the "
        "beneficiary UPI is tradedesk@ybl. Contact on 8123456789."
    ),
}
