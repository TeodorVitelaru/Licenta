import matplotlib.pyplot as plt

matches = [100, 200, 500]

# Accuracy
acc_old = {
    "lgbm": [0.5275, 0.6256, 0.6313],
    "gb":   [0.5873, 0.6408, 0.6357],
    "lr":   [0.5535, 0.6089, 0.6132]
}

acc_new = {
    "lgbm": [0.6222, 0.6589, 0.6456],
    "gb":   [0.6108, 0.6699, 0.6438],
    "lr":   [0.6451, 0.6247, 0.6059]
}

# LogLoss
log_old = {
    "lgbm": [0.9685, 0.8449, 0.7819],
    "gb":   [0.8809, 0.8267, 0.7850],
    "lr":   [0.9455, 0.8189, 0.8160]
}

log_new = {
    "lgbm": [0.8456, 0.7569, 0.7834],
    "gb":   [0.8051, 0.7792, 0.7780],
    "lr":   [0.8318, 0.8109, 0.8398]
}

# ACCURACY LINE PLOT
plt.figure()
plt.plot(matches, acc_old["lgbm"], marker='o',
         linestyle='--', label="LGBM Old")
plt.plot(matches, acc_new["lgbm"], marker='o', label="LGBM New")

plt.plot(matches, acc_old["gb"], marker='s', linestyle='--', label="GB Old")
plt.plot(matches, acc_new["gb"], marker='s', label="GB New")

plt.plot(matches, acc_old["lr"], marker='^', linestyle='--', label="LR Old")
plt.plot(matches, acc_new["lr"], marker='^', label="LR New")

plt.xlabel("Number of Matches")
plt.ylabel("Accuracy")
plt.title("Accuracy vs Dataset Size")
plt.legend()
plt.grid()

plt.savefig("accuracy_vs_matches.png")
plt.show()


# LOG-LOSS LINE PLOT
plt.figure()
plt.plot(matches, log_old["lgbm"], marker='o',
         linestyle='--', label="LGBM Old")
plt.plot(matches, log_new["lgbm"], marker='o', label="LGBM New")

plt.plot(matches, log_old["gb"], marker='s', linestyle='--', label="GB Old")
plt.plot(matches, log_new["gb"], marker='s', label="GB New")

plt.plot(matches, log_old["lr"], marker='^', linestyle='--', label="LR Old")
plt.plot(matches, log_new["lr"], marker='^', label="LR New")

plt.xlabel("Number of Matches")
plt.ylabel("Log-Loss")
plt.title("Log-Loss vs Dataset Size")
plt.legend()
plt.grid()

plt.savefig("logloss_vs_matches.png")
plt.show()


# BAR CHART 
models = ["LGBM", "Gradient Boosting", "Logistic Regression"]

old_500 = [acc_old["lgbm"][2], acc_old["gb"][2], acc_old["lr"][2]]
new_500 = [acc_new["lgbm"][2], acc_new["gb"][2], acc_new["lr"][2]]

x = range(len(models))

plt.figure()
plt.bar(x, old_500, label="Old Features")
plt.bar(x, new_500, bottom=old_500, label="New Features Gain")

plt.xticks(x, models)
plt.ylabel("Accuracy")
plt.title("Model Comparison (500 Matches)")
plt.legend()

plt.savefig("bar_500_matches.png")
plt.show()


# FEATURE IMPACT
gain_lgbm = [new - old for new, old in zip(acc_new["lgbm"], acc_old["lgbm"])]
gain_gb = [new - old for new, old in zip(acc_new["gb"], acc_old["gb"])]
gain_lr = [new - old for new, old in zip(acc_new["lr"], acc_old["lr"])]

plt.figure()
plt.plot(matches, gain_lgbm, marker='o', label="LGBM Gain")
plt.plot(matches, gain_gb, marker='s', label="GB Gain")
plt.plot(matches, gain_lr, marker='^', label="LR Gain")

plt.xlabel("Number of Matches")
plt.ylabel("Accuracy Improvement")
plt.title("Impact of New Features")
plt.legend()
plt.grid()

plt.savefig("feature_impact.png")
plt.show()


# F1 SCORE
f1_old = {
    "lgbm": [0.5265, 0.5867, 0.5780],
    "gb":   [0.5836, 0.5950, 0.5908],
    "lr":   [0.5513, 0.5613, 0.5361]
}

f1_new = {
    "lgbm": [0.5370, 0.6203, 0.5991],
    "gb":   [0.5014, 0.6071, 0.6043],
    "lr":   [0.5949, 0.5596, 0.5595]
}

plt.figure()
plt.plot(matches, f1_old["lgbm"], linestyle='--', marker='o', label="LGBM Old")
plt.plot(matches, f1_new["lgbm"], marker='o', label="LGBM New")

plt.plot(matches, f1_old["gb"], linestyle='--', marker='s', label="GB Old")
plt.plot(matches, f1_new["gb"], marker='s', label="GB New")

plt.plot(matches, f1_old["lr"], linestyle='--', marker='^', label="LR Old")
plt.plot(matches, f1_new["lr"], marker='^', label="LR New")

plt.xlabel("Number of Matches")
plt.ylabel("F1 Macro")
plt.title("F1 Score vs Dataset Size")
plt.legend()
plt.grid()

plt.savefig("f1_vs_matches.png")
plt.show()
