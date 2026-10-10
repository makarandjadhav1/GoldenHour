"""One-time: convert legacy RULES + BRANDS into backend/data/*.json (with examples). Run: python tools/make_rules.py"""
import json, sys
sys.path.insert(0, "legacy/python-prototype")
import scamcore as sc

EX = {
 "credential_request": (["Please share the OTP you just received to confirm.", "Kindly send your CVV to verify the card."],
                        ["Never share your OTP with anyone.", "We will never ask you to share your OTP or PIN."]),
 "remote_access": (["Install AnyDesk so our officer can help you.", "Please start screen sharing now."],
                   ["Your order has shipped.", "Thanks for visiting our branch."]),
 "apk_install": (["Download this apk from the link.", "Install the app from http://x.top/bill.apk"],
                 ["Get our app on the Play Store.", "Your statement is ready."]),
 "digital_arrest": (["You are under digital arrest.", "Transfer the amount to the RBI safe account."],
                    ["Your bank statement is ready.", "Reminder: your appointment is tomorrow."]),
 "isolation": (["Do not disconnect the video call.", "Don't tell anyone about this, including family."],
               ["Please call us back when free.", "Stay safe and drive carefully."]),
 "parcel_drugs": (["A parcel in your name was seized with drugs.", "Illegal items were found in your courier."],
                  ["Your parcel is out for delivery.", "The courier will arrive by 5 pm."]),
 "authority": (["This is the CBI calling about your case.", "Inspector Verma from Cyber Crime Branch."],
               ["Your bank statement is ready.", "Happy birthday from all of us."]),
 "urgency": (["Pay within 2 hours or lose access.", "Final notice, act now."],
             ["Your order will arrive next week.", "See you at the meeting."]),
 "account_threat": (["Your account will be blocked today.", "Your SIM card will be deactivated."],
                    ["Your account statement is ready.", "Welcome to our bank."]),
 "kyc": (["Your KYC update is pending.", "Update your PAN immediately."],
         ["Thanks for visiting the branch.", "Your statement is attached."]),
 "electricity": (["Your electricity bill is unpaid and supply disconnect tonight.", "Your power supply will be cut tonight."],
                 ["Your order is on the way.", "Thanks for your payment."]),
 "investment_promise": (["Guaranteed returns of 30% per day.", "Double your money in a week."],
                        ["Mutual fund investments are subject to market risks.", "Your SIP was processed."]),
 "group_lure": (["Join our VIP group for stock tips.", "You are added to the exclusive channel."],
                ["Join us for lunch tomorrow.", "The class meets on Monday."]),
 "task_job": (["Part-time job: like videos and earn money.", "Work from home and earn Rs 5000 per day."],
              ["We have a full-time opening in Pune.", "Your interview is on Monday."]),
 "upfront_fee": (["Pay a registration fee to withdraw your earnings.", "A refundable deposit is needed to release funds."],
                 ["Your fee receipt is attached.", "Thanks for your payment."]),
 "lottery": (["You have won a lottery of 25 lakh.", "Claim your prize today."],
             ["The lottery results are on the news.", "Congratulations on your promotion."]),
 "loan_app": (["Instant loan approved without documents.", "Pre-approved loan for you."],
              ["Your home loan EMI is due.", "Thank you for repaying."]),
 "refund_trick": (["Your refund is pending, click here.", "The money was wrongly transferred to you."],
                  ["Your order was delivered.", "Thanks for shopping."]),
 "qr_receive": (["Scan this QR to receive the refund.", "Enter your UPI PIN to receive money."],
                ["Scan the QR to pay at the shop.", "Your UPI PIN is private."]),
 "family_emergency": (["Hi mum, I lost my phone, this is my new number.", "Emergency at hospital, send money now."],
                      ["Hi mum, dinner at 8.", "The hospital visit went well."]),
}
rules = []
for r in sc.RULES:
    ex, cex = EX[r.id]
    d = dict(id=r.id, weight=r.weight, category=r.category, critical=r.critical, pattern=r.pattern.pattern,
             flags="i", label={"en": r.label}, why={"en": r.why}, examples=ex, counterExamples=cex)
    if r.unless_before: d["unlessBefore"] = r.unless_before.pattern
    rules.append(d)
json.dump(rules, open("backend/data/rules.json", "w"), indent=1, ensure_ascii=False)
json.dump({"brands": sc.BRANDS, "shorteners": sorted(sc.SHORTENERS), "tlds": sorted(sc.SUSPICIOUS_TLDS)},
          open("backend/data/brands.json", "w"), indent=1)
json.dump({"banks": sc.BANK_ALIASES, "apps": sc.APP_ALIASES}, open("backend/data/banks.json", "w"), indent=1)
json.dump({"advice": {"en": sc.ADVICE}, "typeNames": sc.TYPE_NAMES}, open("backend/data/advice.json", "w"), indent=1)
print(len(rules), "rules")
