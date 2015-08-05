#!/usr/bin/env python

import argparse
import numpy as np
from scipy.stats import norm

# Cancer is over-reported. Adjust to something closer to real values.
# Or say it is a population of industry workers far away.
# Participants are at least 20 y.o
# Health survey probably a lot older than death registry since we have data in
# both

# source: http://www.cancerresearchuk.org/health-professional/cancer-statistics

parser = argparse.ArgumentParser(
    description="Generate data to use by registries",
    formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('-n', '--number', type=int, metavar='N', default=1000,
                    help="Number of individuals",
                    choices=(10, 100, 1000, 10000, 100000, 1000000))
parser.add_argument('-p', '--path', type=str, default="/tmp",
                    help="Output path for csv files")
args = parser.parse_args()

# Warning: When adding more columns, remember to do it both in header and i
# data template
huntfile = open(args.path + "/hunt.csv", "w")
huntfile.write("pid,gender,born,height,weight,bmi,weightd,overweight,"
               "genotyped,training,smoking,drinking\n")
hunt_template = ("1001{id:06d},{gender:d},{born:d},{height:.0f},{weight:.1f},"
                 "{bmi:.1f},{overunderw:.1f},{overw:.1f},{genotyped},"
                 "{training:d},{smoking:d},{drinking:d}\n")

cancerfile = open(args.path + "/cancer.csv", "w")
cancerfile.write("pid,gender,born,cancer,lung_cancer,bowel_cancer,"
                 "breast_cancer,prostate_cancer\n")
cancer_template = ("1001{id:06d},{gender:d},{born:d},{cancer},"
                   "{lc},{bwc},{bc},{pc}\n")

deadfile = open(args.path + "/death.csv", "w")
deadfile.write("pid,gender,born,age,dead,lung_cancer,bowel_cancer,"
               "breast_cancer,prostate_cancer\n")
dead_template = ("1001{id:06d},{gender:d},{born:d},{age},{dead},{ld},{bwd},"
                 "{bd},{pd},{dpr},{dag}\n")

for i in range(0, args.number):
    gender = np.random.choice(2, 1)[0]  # 0=male
    age = np.random.choice(40, 1)[0]+20  # internal
    born = 2010 - age

    # about 75% genotyped?
    genotyped = np.random.choice(2, 1, p=[0.25, 0.75])[0]

    # height: women and men are different
    height = np.random.normal(167, 5) if gender else np.random.normal(180, 5)
    overweight_component = np.random.gamma(6, 1)-6
    weight = height/2.6 + overweight_component * 2
    overw = np.clip(weight - height/2.6, 0, np.inf)
    overunderw = np.absolute(weight - height/2.6)
    bmi = weight / (height/100)**2
    training_effect = (5, 0, -8, 3)

    # training: not, some, often, everyday
    training = np.random.choice(4, 1, p=[0.2, 0.4, 0.3, 0.1])[0]

    # smoking: not, party, some, a lot
    smoking = np.random.choice(4, 1, p=[0.6, 0.1, 0.2, 0.1])[0]

    # drinking: not, seldom, normal, too much
    drinking = np.random.choice(4, 1, p=[0.2, 0.2, 0.5, 0.1])[0]

    # lung cancer: mean(men)=85, sd(men)=15, mean(women)=80, sd(women)=20,
    # p(men)=0.075, p(women)=0.062 warning! p(real)=0.00075
    if gender:
        lung_cancer_probability = norm.cdf(age, 80, 20) * 0.062 * (1 + 4 * smoking)
    else:
        lung_cancer_probability = norm.cdf(age, 85, 20) * 0.075 * (1 + 4 * smoking)
    lung_cancer = np.random.choice(2, 1, p=[1-lung_cancer_probability, lung_cancer_probability])[0]

    # bowel cancer (C18-20): mean=90, sd=20, p(men)=0.075, p(women)=0.057
    # p(real)=0.00075
    # using owerweight, drinking and smoking as causes
    if gender:
        bowel_cancer_probability = norm.cdf(age, 90, 20) * 0.057 * (1 + overw * drinking * smoking)
    else:
        bowel_cancer_probability = norm.cdf(age, 90, 20) * 0.075 * (1 + overw * drinking * smoking)
    bowel_cancer = np.random.choice(2, 1, p=[1-bowel_cancer_probability, bowel_cancer_probability])[0]

    # breast cancer: mean=90, sd=30, p=0.15 p(real)=0.0015
    # training is good
    if gender:
        breast_cancer_probability = norm.cdf(age, 90, 30) * 0.15 * (10 + training_effect[training] + overw * 0.5)
    else:
        breast_cancer_probability = 0
    breast_cancer = np.random.choice(2, 1, p=[1-breast_cancer_probability, breast_cancer_probability])[0]

    # prostate cancer: mean=90, sd=20, p=0.14, p(real)=0.0014
    # training is good
    if gender:
        prostate_cancer_probability = 0
    else:
        prostate_cancer_probability = norm.cdf(age, 90, 40) * 0.14 * (10 + training_effect[training] + overw * 0.5)
    prostate_cancer = np.random.choice(2, 1, p=[1-prostate_cancer_probability, prostate_cancer_probability])[0]

    # dead
    cancer_probability = (lung_cancer_probability +
                          bowel_cancer_probability +
                          breast_cancer_probability +
                          prostate_cancer_probability)
    dead_probability = norm.cdf(age, 100, 35) * 5  # at least 25, age component
    combinded_death_probability = np.clip(
        cancer_probability * 0.2 +
        dead_probability +
        overunderw * 0.001 +
        overw * 0.01 +
        training_effect[training] * 0.01,
        0, 1)
    dead = np.random.choice(
        2, 1,
        p=[1 - combinded_death_probability, combinded_death_probability]
    )[0]

    # print age, dead_probability

    dead_by_lung_cancer_probability = dead * (lung_cancer * 0.95)
    dead_by_lung_cancer = np.random.choice(
        2, 1, p=[1-dead_by_lung_cancer_probability,
                 dead_by_lung_cancer_probability]
    )[0]

    dead_by_bowel_cancer_probability = dead * (bowel_cancer * 0.7)
    dead_by_bowel_cancer = np.random.choice(
        2, 1, p=[1-dead_by_bowel_cancer_probability,
                 dead_by_bowel_cancer_probability]
    )[0]

    dead_by_breast_cancer_probability = dead * (breast_cancer * 0.8)
    dead_by_breast_cancer = np.random.choice(
        2, 1, p=[1-dead_by_breast_cancer_probability,
                 dead_by_breast_cancer_probability]
    )[0]

    dead_by_prostate_cancer_probability = dead * (prostate_cancer * 0.9)
    dead_by_prostate_cancer = np.random.choice(
        2, 1, p=[1-dead_by_prostate_cancer_probability,
                 dead_by_prostate_cancer_probability]
    )[0]

    # print dead_probability, combinded_death_probability,
    # dead_by_lung_cancer_probability, dead_by_bowel_cancer_probability,
    # dead_by_breast_cancer_probability, dead_by_prostate_cancer_probability

    cancer = lung_cancer or bowel_cancer or breast_cancer or prostate_cancer

    values = dict(id=i, gender=gender, born=born, height=height, weight=weight,
                  training=training, smoking=smoking, drinking=drinking,
                  bmi=bmi, overunderw=overunderw, overw=overw,
                  genotyped=genotyped, cancer=cancer, lc=lung_cancer,
                  bc=breast_cancer, pc=prostate_cancer, bwc=bowel_cancer,
                  age=age, dead=dead, ld=dead_by_lung_cancer,
                  bwd=dead_by_bowel_cancer, bd=dead_by_breast_cancer,
                  pd=dead_by_prostate_cancer, dpr=combinded_death_probability,
                  dag=dead_probability)


    # print "1001{id:06d},{gender:d},{born:d},{height:.0f},{weight:.1f},{bmi:.1f},{overunderw:.1f},{overw:.1f},{genotyped},{training:d},{smoking:d},{drinking:d},{lc},{bwc},{bc},{pc},{age},{ld},{bwd},{bd},{pd},{dead},{dpr},{dag}".replace(",", "\t").format(**values)

    if np.random.choice(2, 1):  # 50% chance of being in hunt
        huntfile.write(hunt_template.format(**values))

    if cancer:  # everybody with cancer
        cancerfile.write(cancer_template.format(**values))

    if dead:  # everybody dead
        deadfile.write(dead_template.format(**values))
