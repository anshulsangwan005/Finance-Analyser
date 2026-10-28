"""Train and save the categorization model. Run: python train.py"""
from app.ml.categorizer import train

if __name__ == "__main__":
    m = train(save=True, verbose=True)
    print("Saved model.", m)
