"""Synthetic UPI/bank-style transaction descriptions for training the categorizer (Risk R1 mitigation)."""
import random

MERCHANTS = {
    "Food": ["swiggy", "zomato", "dominos pizza", "mcdonalds", "kfc", "starbucks", "cafe coffee day", "burger king",
             "haldirams", "chaayos", "subway", "pizza hut", "box8", "behrouz biryani", "college canteen", "campus cafe"],
    "Groceries": ["bigbasket", "blinkit", "zepto", "dmart", "reliance fresh", "more supermarket", "grofers",
                  "jiomart", "instamart", "spencers", "vegetable vendor", "kirana store", "milk dairy"],
    "Transport": ["uber", "ola cabs", "rapido", "irctc", "delhi metro", "dmrc", "indian oil petrol", "hp petrol pump",
                  "bharat petroleum", "fastag", "redbus", "namma metro", "auto rickshaw", "shell fuel"],
    "Shopping": ["amazon", "flipkart", "myntra", "ajio", "nykaa", "meesho", "decathlon", "croma", "reliance digital",
                 "zara", "h&m", "lifestyle stores", "westside", "pantaloons", "tata cliq"],
    "Bills": ["airtel recharge", "jio prepaid", "vodafone idea", "bsnl broadband", "electricity bill bses", "tata power",
              "gas cylinder indane", "water bill", "act fibernet", "dth tata play", "postpaid bill", "insurance premium lic"],
    "Entertainment": ["netflix", "spotify", "bookmyshow", "pvr cinemas", "inox", "hotstar", "amazon prime", "youtube premium",
                      "steam games", "playstation store", "sony liv", "gaana", "zee5", "gaming zone"],
    "Health": ["apollo pharmacy", "1mg", "pharmeasy", "medplus", "practo", "fortis hospital", "max hospital",
               "cult fit", "gym membership", "diagnostic lab", "dr lal pathlabs", "dental clinic", "netmeds"],
    "Education": ["udemy", "coursera", "byjus", "unacademy", "college fee", "bennett university fee", "exam fee",
                  "book store", "amazon kindle", "upgrad", "skillshare", "library fine", "stationery shop"],
    "Rent": ["house rent", "pg rent", "hostel fee", "landlord", "rent payment", "nobroker rent", "flat rent monthly",
             "hostel mess rent", "room rent"],
    "Travel": ["makemytrip", "goibibo", "indigo airlines", "air india", "oyo rooms", "airbnb", "cleartrip",
               "yatra", "booking.com", "vistara", "spicejet", "treebo hotels", "thomas cook", "goa resort"],
    "Transfers": ["transfer to friend", "sent to mom", "upi to rahul", "paid to amit", "neft self", "imps transfer",
                  "atm cash withdrawal", "cash withdrawal", "wallet topup", "paytm wallet", "gift to sister", "split dinner share"],
    "Other": ["miscellaneous", "bank charges", "annual fee", "service charge", "donation", "temple", "laundry", "salon",
              "courier charges", "gst charge", "sms charges", "stamp duty", "repair work", "hardware store"],
}
INCOME_MERCHANTS = ["salary", "stipend", "freelance payment", "interest credit", "refund", "cashback", "dividend"]

PATTERNS = [
    "UPI/{m}/{n}/{x}", "UPI-{m}-{n}@okaxis", "POS {n} {m}", "{m}", "{m} {x}", "NEFT-{m}-{n}",
    "IMPS/{n}/{m}", "PAYMENT TO {m} {n}", "{m} PVT LTD", "UPI/{n}/{m}/Payment", "DEBIT CARD {m} {n}",
]
SUFFIXES = ["order", "payment", "bill", "txn", "ref", "app", "online", "india"]


def make_description(merchant: str, rng: random.Random) -> str:
    p = rng.choice(PATTERNS)
    d = p.format(m=merchant.upper() if rng.random() < 0.6 else merchant, n=rng.randint(100000, 999999),
                 x=rng.choice(SUFFIXES))
    if rng.random() < 0.15:  # typos / truncation noise
        i = rng.randrange(len(d))
        d = d[:i] + d[i + 1:]
    return d


def generate(n_per_class: int = 220, seed: int = 42):
    rng = random.Random(seed)
    texts, labels = [], []
    for cat, merchants in MERCHANTS.items():
        for _ in range(n_per_class):
            texts.append(make_description(rng.choice(merchants), rng))
            labels.append(cat)
    return texts, labels
