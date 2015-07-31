import numpy as np
from scipy.stats import norm

# source: http://www.cancerresearchuk.org/health-professional/cancer-statistics

print "id,gender,born,height,weight,genotyped,training,smoking,drinking,bmi,lc,tc,bc,pc,bwc"
for i in range(1, 10000):
    gender = np.random.choice(2, 1)[0]  # 0=male
    age = np.random.choice(40, 1)[0]+20  # internal
    born = age + 1930

    # about 75% genotyped?
    genotyped = np.random.choice(2, 1, p=[0.25, 0.75])[0]

    # height: women and men are different
    height = np.random.normal(167, 5) if gender else np.random.normal(180, 5)
    weight = np.random.normal(height/2.25, 10)
    bmi = weight / (height/100)**2

    # training: not, some, often, everyday
    training = np.random.choice(4, 1, p=[0.2, 0.4, 0.3, 0.1])[0]

    # smoking: not, party, some, a lot
    smoking = np.random.choice(4, 1, p=[0.6, 0.1, 0.2, 0.1])[0]

    # drinking: not, seldom, normal, too much
    drinking = np.random.choice(4, 1, p=[0.2, 0.2, 0.5, 0.1])[0]

    # lung cancer: mean(men)=85, sd(men)=15, mean(women)=80, sd(women)=20, p(men)=0.075, p(women)=0.062 warning! p(real)=0.00075
    if gender:
        lung_cancer_probability = norm.cdf(age, 80, 20) * 0.062
    else:
        lung_cancer_probability = norm.cdf(age, 85, 20) * 0.075
    lung_cancer = np.random.choice(2, 1, p=[1-lung_cancer_probability, lung_cancer_probability])[0]

    # bowel cancer (C18-20): mean=90, sd=20, p(men)=0.075, p(women)=0.057 p(real)=0.00075
    if gender:
        bowel_cancer_probability = norm.cdf(age, 90, 20) * 0.057
    else:
        bowel_cancer_probability = norm.cdf(age, 90, 20) * 0.075
    bowel_cancer = np.random.choice(2, 1, p=[1-bowel_cancer_probability, bowel_cancer_probability])[0]

    # breast cancer: mean=90, sd=30, p=0.15 p(real)=0.0015
    if gender:
        breast_cancer_probability = norm.cdf(age, 90, 30) * 0.15
        breast_cancer = np.random.choice(2, 1, p=[1-breast_cancer_probability, breast_cancer_probability])[0]
    else:
        breast_cancer = 0

    # prostate cancer: mean=90, sd=20, p=0.14, p(real)=0.0014
    if gender:
        prostate_cancer = 0
    else:
        prostate_cancer_probability = norm.cdf(age, 90, 40) * 0.14
        prostate_cancer = np.random.choice(2, 1, p=[1-prostate_cancer_probability, prostate_cancer_probability])[0]

    cancer = lung_cancer or bowel_cancer or breast_cancer or prostate_cancer
    if cancer:
        print "1001{id:06d},{gender:d},{born:d},{height:.0f},{weight:.0f},{genotyped},{training:d},{smoking:d},{drinking:d},{bmi:.1f},{lc},{bc},{pc},{bwc}".format(
            id=i, gender=gender, born=born, height=height, weight=weight, training=training, smoking=smoking, drinking=drinking, bmi=bmi, genotyped=genotyped,
            lc=lung_cancer, bc=breast_cancer, pc=prostate_cancer, bwc=bowel_cancer)
