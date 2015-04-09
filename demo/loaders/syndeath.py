#
#   The contents of this file are subject to the HACOS License Version 1.2
#   (the "License"); you may not use this file except in compliance with
#   the License.  Software distributed under the License is distributed
#   on an "AS IS" basis, WITHOUT WARRANTY OF ANY KIND, either express or
#   implied. See the LICENSE file for the specific language governing
#   rights and limitations under the License.  The Original Software
#   is "NetEpi Analysis". The Initial Developer of the Original
#   Software is the Health Administration Corporation, incorporated in
#   the State of New South Wales, Australia.
#
#   Copyright (C) 2004,2005 Health Administration Corporation.
#   All Rights Reserved.
#
#   Define and load new WHO World Standard Population data
#
# $Id: syndeath.py 2626 2007-03-09 04:35:54Z andrewm $
# $Source: /usr/local/cvsroot/NSWDoH/SOOMv0/demo/loaders/syndeath.py,v $

# Python standard modules
import os
import csv

# 3rd Party Modules
# http://www.pfdubois.com/numpy/
import Numeric, MA

# SOOM modules
from SOOMv0 import *
from SOOMv0.Sources.CSV import *

agegrp_outtrans = {
    1: '0-4 yrs',
    2: '5-9 yrs',
    3: '10-14 yrs',
    4: '15-19 yrs',
    5: '20-24 yrs',
    6: '25-29 yrs',
    7: '30-34 yrs',
    8: '35-39 yrs',
    9: '40-44 yrs',
    10: '45-49 yrs',
    11: '50-54 yrs',
    12: '55-59 yrs',
    13: '60-64 yrs',
    14: '65-69 yrs',
    15: '70-74 yrs',
    16: '75-79 yrs',
    17: '80-84 yrs',
    18: '85+ yrs',
    19: 'Invalid Data',
    20: 'Unknown',
}

causeofdeath_outtrans = {
    1: 'Malignant neoplasm of pancreas (ICD9 157)',
    2: 'Railway accidents (ICD9 E800-E807)',
    3: 'Benign neoplasm of nervous system (ICD9 225)',
    4: 'Meningitis (ICD9 320-322)',
    5: 'Retention of urine (ICD9 788.2)',
    6: 'Sudden infant death syndrome (ICD9 798.0)',
    7: 'Tuberculosis of genitourinary system (ICD9 016)',
    8: 'Other congenital anomalies of musculoskeletal system (ICD9 754.0-754.2,754.4-756)',
    9: 'Other chronic obstructive pulmonary disease (ICD9 495,496)',
    10: 'Affective psychoses (ICD9 296)',
    11: 'Spontaneous abortion (ICD9 634)',
    12: 'Malignant neoplasm of larynx (ICD9 161)',
    13: 'Late effects of tuberculosis (ICD9 137)',
    14: 'Epilepsy (ICD9 345)',
    15: 'Abdominal pain (ICD9 789.0)',
    16: 'Subarachnoid haemorrhage (ICD9 430)',
    17: 'Senility without mention of psychosis (ICD9 797)',
    18: 'Alcohol dependence syndrome (ICD9 303)',
    19: 'Benign neoplasm of ovary (ICD9 220)',
    20: 'Arthropod-borne encephalitis (ICD9 062-064)',
    21: 'Accidents caused by firearm missile (ICD9 E922)',
    22: 'Acute but ill-defined cerebrovascular disease (ICD9 436)',
    23: 'Injury undetermined whether accidentally or purposely inflicted (ICD9 E980-E989)',
    24: 'Malignant neoplasm of cervix uteri (ICD9 180)',
    25: 'Syphilis (ICD9 090-097)',
    26: 'Ill-defined intestinal infections (ICD9 009)',
    27: 'Rheumatoid arthritis, except spine (ICD9 714)',
    28: 'Senile and presenile organic psychotic conditions (ICD9 290)',
    29: 'Spina bifida and hydrocephalus (ICD9 741,742.3)',
    30: 'Malignant neoplasm of colon (ICD9 153)',
    31: 'Intracerebral and other intracranial haemorrhage (ICD9 431,432)',
    32: 'Other acute upper respiratory infections (ICD9 460-462,465)',
    33: 'Accidents due to natural and environmental factors (ICD9 E900-E909)',
    34: 'Hyperplasia of prostate (ICD9 600)',
    35: 'Ankylosing spondylitis (ICD9 720.0)',
    36: 'Pneumoconiosis and other lung disease due to external agents (ICD9 500-508)',
    37: 'Accidental poisoning by gases and vapours (ICD9 E867-E869)',
    38: 'Chronic liver disease and cirrhosis (ICD9 571)',
    39: 'Acute myocardial infarction (ICD9 410)',
    40: 'Cardiac dysrhythmias (ICD9 427)',
    41: 'Meningococcal infection (ICD9 036)',
    42: 'Other psychoses (ICD9 291-294,297-299)',
    43: 'Malignant neoplasm of small intestine, including duodenum (ICD9 152)',
    44: 'Other degenerative and hereditary disorders of the CNS (ICD9 330,331,333-336)',
    45: 'Measles (ICD9 055)',
    46: 'Influenza (ICD9 487)',
    47: 'Hyperlipoproteinaemia (ICD9 272.0,272.1)',
    48: 'Diphtheria (ICD9 032)',
    49: 'Inflammatory diseases of pelvic cellular tissue and peritoneum (ICD9 614.3-614.9)',
    50: 'Cerebral atherosclerosis (ICD9 437.0)',
    51: 'Diseases of oesophagus (ICD9 530)',
    52: 'Other arthropathies (ICD9 710-713,715,716)',
    53: 'Nutritional marasmus (ICD9 261)',
    54: 'Diseases of breast (ICD9 610,611)',
    55: 'Malignant neoplasm of stomach (ICD9 151)',
    56: 'Benign neoplasm of thyroid (ICD9 226)',
    57: 'Late effects of acute poliomyelitis (ICD9 138)',
    58: 'Other dorsopathies (ICD9 720.1-724)',
    59: 'Hypertensive heart disease (ICD9 402,404)',
    60: 'Strabismus and other disorders of binocular eye movements (ICD9 378)',
    61: 'Toxaemia of pregnancy (ICD9 642.4-642.9,643)',
    62: 'Mental retardation (ICD9 317-319)',
    63: 'Malignant neoplasm of testis (ICD9 186)',
    64: 'Arterial embolism and thrombosis (ICD9 444)',
    65: 'Septicaemia (ICD9 038)',
    66: 'Pulmonary embolism (ICD9 415.1)',
    67: 'Other rickettsiosis (ICD9 081-083)',
    68: 'Pyrexia of unknown origin (ICD9 780.6)',
    69: 'Intestinal obstruction without mention of hernia (ICD9 560)',
    70: 'Pleurisy (ICD9 511)',
    71: 'Haemolytic disease of fetus or newborn (ICD9 773)',
    72: "Parkinson's disease (ICD9 332)",
    73: 'Ulcer of stomach and duodenum (ICD9 531-533)',
    74: 'Infections of kidney (ICD9 590)',
    75: 'Viral hepatitis (ICD9 070)',
    76: 'Blindness and low vision (ICD9 369)',
    77: 'Benign neoplasm of skin (ICD9 216)',
    78: "Hodgkin's disease (ICD9 201)",
    79: 'Intestinal infections due to other specified organism (ICD9 007,008)',
    80: 'Whooping cough (ICD9 033)',
    81: 'Benign neoplasm of kidney and other urinary organs (ICD9 223)',
    82: 'Birth trauma (ICD9 767)',
    83: 'Cholelithiasis and cholecystitis (ICD9 574-575.1)',
    84: 'Diseases of teeth and supporting structures (ICD9 520-525)',
    85: 'Malignant neoplasm of ovary and other uterine adnexa (ICD9 183)',
    86: 'Other respiratory tuberculosis (ICD9 010,012)',
    87: 'Malignant neoplasm of rectum, rectosigmoid junction and anus (ICD9 154)',
    88: 'Malignant neoplasm of liver, specified as primary (ICD9 155.0)',
    89: 'Pneumonia (ICD9 480-486)',
    90: 'Nephritis, nephrotic syndrome and nephrosis (ICD9 580-589)',
    91: 'Injury resulting from operation of war (ICD9 E990-E999)',
    92: 'Amoebiasis (ICD9 006)',
    93: 'Cystitis (ICD9 595)',
    94: 'Malignant neoplasm of uterus, other and unspecified (ICD9 179,182)',
    95: 'Malignant neoplasm of trachea, bronchus and lung (ICD9 162)',
    96: 'Other protein-calorie malnutrition (ICD9 262,263)',
    97: 'Food poisoning (ICD9 003,005)',
    98: 'Uterovaginal prolapse (ICD9 618)',
    99: 'Urinary calculus (ICD9 592,594)',
    100: 'Appendicitis (ICD9 540-543)',
    101: 'Air and space transport accidents (ICD9 E840-E845)',
    102: 'Kwashiorkor (ICD9 260)',
    103: 'Malignant neoplasm of prostate (ICD9 185)',
    104: 'Accidental poisoning by drugs,medicaments and biologicals (ICD9 E850-E858)',
    105: 'Hernia of abdominal cavity (ICD9 550-553)',
    106: 'Leukaemia (ICD9 204-208)',
    107: 'Respiratory failure (ICD9 799.1)',
    108: 'Mycosis (ICD9 110-118)',
    109: 'Congenital anomalies of heart and circulatory system (ICD9 745-747)',
    110: 'Inflammatory diseases of uterus, vagina and vulva (ICD9 615,616)',
    111: 'Bronchitis, chronic and unspecified, emphysema and asthma (ICD9 490-493)',
    112: 'Motor vehicle traffic accidents (ICD9 E810-E819)',
    113: 'Malignant neoplasm of placenta (ICD9 181)',
    114: 'Rabies (ICD9 071)',
    115: 'Hypoxia, birth asphyxia and other respiratory conditions (ICD9 768-770)',
    116: 'Shigellosis (ICD9 004)',
    117: 'Diverticula of intestine (ICD9 562)',
    118: 'Rubella (ICD9 056)',
    119: 'Atherosclerosis (ICD9 440)',
    120: 'Anaemias (ICD9 280-285)',
    121: 'Streptococcal sore throat, scarlatina and erysipelas (ICD9 034,035)',
    122: 'Accidents caused by machinery and by cutting/piercing instruments (ICD9 E919,E920)',
    123: 'Otitis media and mastoiditis (ICD9 381-383)',
    124: 'Other malignant neoplasm of skin (ICD9 173)',
    125: 'Infantile cerebral palsy and other paralytic syndromes (ICD9 343,344)',
    126: 'Bronchiectasis (ICD9 494)',
    127: 'Neurotic and personality disorders (ICD9 300,301)',
    128: 'Osteomyelitis, periostitis and other infections involving bone (ICD9 730)',
    129: 'Rheumatism, excluding the back (ICD9 725-729)',
    130: 'Other road vehicle accidents (ICD9 E826-E829)',
    131: 'Disorders of thyroid gland (ICD9 240-246)',
    132: 'Other diseases of arteries, arterioles and capillaries (ICD9 441-443,446-448)',
    133: 'Other functional digestive disorders (ICD9 564)',
    134: 'Other deformities of central nervous system (ICD9 740,742.0-742.2,742.4-742.9)',
    135: 'Tuberculosis of meninges and central nervous system (ICD9 013)',
    136: 'Malignant neoplasm of brain (ICD9 191)',
    137: 'Accidental poisoning by other solid and liquid substances (ICD9 E860-E866)',
    138: 'Benign neoplasm of uterus (ICD9 218,219)',
    139: 'Acute laryngitis and tracheitis (ICD9 464)',
    140: 'Malignant neoplasm of bladder (ICD9 188)',
    141: 'Multiple sclerosis (ICD9 340)',
    142: 'Schistosomiasis (ICD9 120)',
    143: 'Varicose veins of lower extremities (ICD9 454)',
    144: 'Acute bronchitis and bronchiolitis (ICD9 466)',
    145: 'Phlebitis, thrombophlebitis, venous embolism and thrombosis (ICD9 451-453)',
    146: 'Salpingitis and oophoritis (ICD9 614.0-614.2)',
    147: 'Leishmaniasis (ICD9 085)',
    148: 'Obesity of non-endocrine origin (ICD9 278.0)',
    149: 'Obstructed labour (ICD9 660)',
    150: 'Water transport accidents (ICD9 E830-E838)',
    151: 'Redundant prepuce and phimosis (ICD9 605)',
    152: 'Acute tonsillitis (ICD9 463)',
    153: 'Slow fetal growth, fetal malnutrition and immaturity (ICD9 764,765)',
    154: 'Drug dependence (ICD9 304)',
    155: 'Schizophrenic psychoses (ICD9 295)',
    156: 'Other deformities of digestive system (ICD9 750,751)',
    157: 'Echinococcosis (ICD9 122)',
    158: 'Non-syphilitic spirochaetal diseases (ICD9 100-104)',
    159: 'Infections of skin and subcutaneous tissue (ICD9 680-686)',
    160: 'Avitaminosis (ICD9 264-269)',
    161: 'Filarial infection and dracontiasis (ICD9 125)',
    162: 'Other helminthiasis (ICD9 121,123,124,127-129)',
    163: 'Acute rheumatic fever (ICD9 390-392)',
    164: 'Tuberculosis of intestines, peritoneum and mesenteric glands (ICD9 014)',
    165: 'Obstetric complications affecting fetus or newborn (ICD9 761-763)',
    166: 'Cerebral infarction (ICD9 433,434)',
    167: 'Malignant neoplasm of bone and articular cartilage (ICD9 170)',
    168: 'Other disorders of joints (ICD9 717-719)',
    169: 'Chronic rheumatic heart disease (ICD9 393-398)',
    170: 'Malaria (ICD9 084)',
    171: 'Tetanus (ICD9 037)',
    172: 'Haemorrhoids (ICD9 455)',
    173: 'Legally induced abortion (ICD9 635)',
    174: 'Accidental drawning and submersion (ICD9 E910)',
    175: 'Malignant neoplasm of oesophagus (ICD9 150)',
    176: 'Foreign body accidentally entering orifice (ICD9 E914,E915)',
    177: 'Pulmonary tuberculosis (ICD9 011)',
    178: 'Chronic pharyngitis, nasopharyngitis and sinusitis (ICD9 472, 473)',
    179: 'Diabetes mellitus (ICD9 250)',
    180: 'Malignant neoplasm of female breast (ICD9 174)',
    181: 'Malignant melanoma of skin (ICD9 172)',
    182: 'Tuberculosis of bones and joints (ICD9 015)',
    183: 'Trypanosomiasis (ICD9 086)',
    184: 'Haemorrhage of pregnancy and childbirth (ICD9 640,641,666)',
}

sex_outtrans = {
    1: 'Male',
    2: 'Female',
    9: 'Unknown',
}

region_outtrans = {
    1: 'Region A',
    2: 'Region B',
    3: 'Region C',
    4: 'Region D',
    5: 'Region E',
    6: 'Region F',
    7: 'Region G',
    8: 'Region H',
    9: 'Region I',
   10: 'Region J',
   11: 'Region K',
   12: 'Region L',
   13: 'Region M',
   14: 'Region N',
   15: 'Region O',
   16: 'Region P',
   17: 'Region Q',
   18: 'Unknown'
}

def make_death(options):
    ds = makedataset('syndeath',label='Synthetic Death Dataset')
    ds.addcolumn('agegrp', label='Age group',
                 datatype='int', coltype='ordinal',
                 outtrans=agegrp_outtrans)
    ds.addcolumn('sex', label='Sex',
                 datatype='int', coltype='categorical',
                 outtrans=sex_outtrans)
    ds.addcolumn('region', label='Region',
                 datatype='int', coltype='categorical',
                 outtrans=region_outtrans)
    ds.addcolumn('year', label='Year of death',
                 datatype='int', coltype='ordinal')
    ds.addcolumn('causeofdeath', label='Cause of death',
                 datatype='int', coltype='categorical',
                 outtrans=causeofdeath_outtrans)
    if options.verbose:
        print ds
    return ds

def load_death_source(ds, options):
    from syndeath_expand import syndeath_expand
    syndeath_expand(options.datadir, options.scratchdir, options.verbose)
    filename = os.path.join(options.scratchdir, 'synthetic_deaths.csv.gz')
    source = HeaderCSVDataSource('syndeath', [], filename=filename)
    ds.initialise()
    ds.loaddata(source,
                chunkrows=options.chunkrows,
                rowlimit=options.rowlimit)
    ds.finalise()

def make_pop(options):
    ds = makedataset('synpop',label='Synthetic Population Dataset',summary=True)
    ds.addcolumn('agegrp', label='Age group',
                 datatype='int', coltype='ordinal',
                 outtrans=agegrp_outtrans)
    ds.addcolumn('sex', label='Sex',
                 datatype='int', coltype='categorical',
                 outtrans=sex_outtrans)
    ds.addcolumn('region', label='Region',
                 datatype='int', coltype='categorical',
                 outtrans=region_outtrans)
    ds.addcolumn('year', label='Year',
                 datatype='int', coltype='ordinal')
    ds.addcolumn('pop', label='Population',
                 datatype='int', coltype='scalar')
    if options.verbose:
        print ds
    return ds


def load_pop_source(ds, options):
    filename = os.path.join(options.datadir, 'synthetic_pops.csv.gz')
    source = HeaderCSVDataSource('synpop', [], filename=filename)
    ds.initialise()
    ds.loaddata(source,
                chunkrows=options.chunkrows,
                rowlimit=options.rowlimit)
    ds.finalise()

def make_stdpop_mf(options):
    ds = makedataset('aus01stdpop_mf',label='Australian 2001 Standard Population (males and females)',
                     summary=True)
    ds.addcolumn('agegrp', label='Age group',
                 datatype='int', coltype='ordinal',
                 outtrans=agegrp_outtrans)
    ds.addcolumn('sex', label='Sex',
                 datatype='int', coltype='categorical',
                 outtrans=sex_outtrans)
    ds.addcolumn('pop', label='Population',
                 datatype='int', coltype='scalar')
    if options.verbose:
        print ds
    return ds

def load_stdpop_mf_source(ds, options):
    filename = os.path.join(options.datadir, 'aus01stdpop_mf.csv')
    source = HeaderCSVDataSource('synstdpop', [], filename=filename)
    ds.initialise()
    ds.loaddata(source,
                chunkrows=options.chunkrows,
                rowlimit=options.rowlimit)
    ds.finalise()

def make_stdpop(options):
    ds = makedataset('aus01stdpop',label='Australian 2001 Standard Population',
                     summary=True)
    ds.addcolumn('agegrp', label='Age group',
                 datatype='int', coltype='ordinal',
                 outtrans=agegrp_outtrans)
    ds.addcolumn('pop', label='Population',
                 datatype='int', coltype='scalar')
    if options.verbose:
        print ds
    return ds

def load_stdpop_source(ds, options):
    filename = os.path.join(options.datadir, 'aus01stdpop.csv')
    source = HeaderCSVDataSource('synstdpop', [], filename=filename)
    ds.initialise()
    ds.loaddata(source,
                chunkrows=options.chunkrows,
                rowlimit=options.rowlimit)
    ds.finalise()


def load(options):
    ds = make_death(options)
    load_death_source(ds, options)
    ds.save()

    ds = make_pop(options)
    load_pop_source(ds, options)
    ds.save()

    ds = make_stdpop_mf(options)
    load_stdpop_mf_source(ds, options)
    ds.save()

    ds = make_stdpop(options)
    load_stdpop_source(ds, options)
    ds.save()
