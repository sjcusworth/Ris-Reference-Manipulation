from re import findall
from random import shuffle, seed
from tqdm import tqdm

seed(117)

OUT_DIR = "screening/"

varFields = {
        "proquest": {
            "doi": "DO", #e.g. https://doi.org/10.3390/cancers13153704
            "title": "T1",
            "author": "AU", #e.g. Monga, Neerav
            "year": "DA",
            },
        "scopus": {
            "doi": "DO", #e.g. 10.4103/jcrt.JCRT_782_23
            "title": "TI",
            "author": "AU", # e.g. Seminog, O.O.
            "year": "PY",
            },
        "webOfScience": {
            "doi": "DO", #e.g. 10.1007/s00277-016-2787-7
            "title": "TI",
            "author": "AU", #e.g. Dahlström, J
            "year": "PY",
            },
        "campbell": {
            "doi": "DO", #e.g. https://doi.org/10.4073/csr.2015.5
            "title": "T1",
            "author": "AU", #e.g. Fong, Carlton J.
            "year": "PY",
            },
        "cochrane": {
            "doi": "DO", #e.g. 10.1002/cca.4108
            "title": "TI",
            "author": "AU", #e.g. El‐Nakeep, Sarah
            "year": "PY",
            },
        "epistemonikos": {
            "doi": "DO", #e.g. 10.1111/bjh.12562
            "title": "TI",
            "author": "AU", #e.g. Shirley MH
            "year": "PY",
            },
        "ovidEbmr": {
            "doi": "DO", #e.g. https://dx.doi.org/10.1016/S2352-3026(23)00212-0
            "title": "T1",
            "author": "A1", #e.g. Pasic, Ivan
            "year": "Y1",
            },
        "ovidEbmrEmbase": {
            "doi": "DO", #e.g. https://dx.doi.org/10.1101/2023.12.15.571872
            "title": "T1",
            "author": "A1", #e.g. Poon G.
            "year": "Y1",
            },
        "pubmed": {
            "doi": "LID", #e.g. 10.1016/S2352-3026(22)00291-5 [doi] #NOTE: needs to look for the LID field specifically ending with '[doi]' (can be multiple LID fields)
            "title": "TI",
            "author": "AU", #e.g. Hu Y
            "year": "DP",
            },
        "healthEvidence": {
            "doi": "UR", #e.g. https://doi.org/10.1002/14651858.CD004407.pub3 #NOTE: can be multiple UR fields
            "title": "T1",
            "author": "A1", #e.g. Gonzalez SA
            "year": "Y1",
            },
        }

# NOTE: Needs to ensure records without a doi field aren't automatically removed

class RisReader:
    def __init__(self, filename):
        self.filename = filename

    def read_ris(self):
        with open(self.filename, 'r') as file:
            content = file.read()

        # Split the content by blank lines
        references = content.split('\n\n')

        if references[-1] == "":
            references.pop(len(references)-1)

        # Initialize an empty list to hold all references
        all_references = []

        # Loop through each reference
        for reference in references:
            # Split the reference into lines
            lines = reference.split('\n')

            # Initialize an empty dictionary to hold the current reference
            current_reference = {}
            current_reference_raw = []
            currRef_keyCounts = {}

            # Loop through each line
            for line in lines:

                current_reference_raw.append(line)

                if line.startswith("ER"):
                    key, value = "ER", ""
                else:
                    # Split the line into key and value

                    #assuming that fields that don't abide by normal format can be ignored
                    #e.g. 'key: value' not 'key - value'
                    if len(line.split("-", 1)) == 1:
                        continue
                    key, value = line.split('-', 1)

                    #remove whitespace surrounding '-'
                    key = "".join([x for x in key if x != " "])
                    if value[0] == " ":
                        value = value[1:]
                    #remove trailing whitespace
                    value = value.rstrip()

                # Add the key-value pair to the current reference
                if key not in currRef_keyCounts.keys():
                    currRef_keyCounts[key] = 0
                else:
                    currRef_keyCounts[key]+=1
                    key = f"{key}_{currRef_keyCounts[key]}"

                current_reference[key] = value

            # Add the current reference to the list of all references
            if not current_reference_raw[-1].startswith("ER"):
                current_reference_raw.append("ER  -")

            all_references.append(tuple([current_reference, current_reference_raw]))

        return all_references


FILE_SUFF = "_yearFilt_2010.ris"
DOI_PREF = "org/"

dict_refs = {}
dups = []
database_dups = {}
database_refs = {}
noDoi = []
noTitle_withDoi = []
noAuthor_withDoiTitle = []
noYear_withDoiTitleAuthor = []

matchingUids = {}

raw_refs = []

for dir_, fields_ in varFields.items():
    print(dir_)
    database_dups[dir_] = 0
    database_refs[dir_] = 0

    file_ = f"{dir_}/{dir_}{FILE_SUFF}"
    ris = RisReader(file_).read_ris()

    for ref_, ref_raw_ in ris:
        find_doi = [x for x in ref_.keys() if x.startswith(varFields[dir_]["doi"])]

        if len(find_doi)==0:
            noDoi.append(ref_)
            raw_refs.append(ref_raw_)
            continue
        elif len(find_doi)>1:
            dois = {x:y for x,y in ref_.items() if x in find_doi}
            doi = list(dois.values())
        else:
            doi = [ref_[varFields[dir_]["doi"]]]

        if varFields[dir_]["title"] not in ref_.keys():
            noTitle_withDoi.append(ref_)
            raw_refs.append(ref_raw_)
            continue
        title = ref_[varFields[dir_]["title"]]
        #Assumes that titles that are the same once all non-alphanumeric characters removed are the same
        title = "".join([x.lower() for x in title if x.isalnum()])

        if varFields[dir_]["author"] not in ref_.keys():
            noAuthor_withDoiTitle.append(ref_)
            raw_refs.append(ref_raw_)
            continue
        author = ref_[varFields[dir_]["author"]]
        author = author.split(" ")
        if len(author) == 1:
            author = author[0]
        else:
            author[0] = "".join([x.lower() for x in author[0] if x.isalnum()])
            author[1] = author[1].upper()[0]
            author = f"{author[0]}{author[1]}"

        if varFields[dir_]["year"] not in ref_.keys():
            noYear_withDoiTitleAuthor.append(ref_)
            raw_refs.append(ref_raw_)
            continue
        year = ref_[varFields[dir_]["year"]]
        year = findall(r'.*?(\d{4}).*', year)[0]


        uid = f"{title} {author} {year}"

        #format doi
        for i, d in enumerate(doi.copy()):
            ind_prefix = d.find(DOI_PREF)
            if ind_prefix != -1:
                doi[i] = d[ind_prefix+len(DOI_PREF):]

            #hardcoded formatting of pubmed refs
            if d.endswith(" [doi]"):
                doi[i] = d[:-6]

        #dict_refs.values if a list of lists of dois
        #the above is flattened, then each doi in doi is checked for whether it is in the flattened list, returning True if so
        find_doi = [True if x in refs else False for x in doi for refs in [j for y in dict_refs.values() for j in y]]
        if not any(find_doi):
            #NOTE: Assumes each reference has all dois allocated to a title, author
                # NOTE: Assumes title + primary author surname + 1st initial + year is unique to a paper
            if uid in dict_refs.keys():
                #print(f"New: {uid} {doi}")
                #print(f"Existing: {dict_refs[uid]}")
                dict_refs[uid] = dict_refs[uid] + doi
                matchingUids[uid] = dict_refs[uid]
            else:
                dict_refs[uid] = doi
                database_refs[dir_]+=1
                raw_refs.append(ref_raw_)
        else:
            dups.append(tuple([doi, uid]))
            database_dups[dir_]+=1

print(f"Total refs: {sum(list(database_refs.values())) + len(noTitle_withDoi) + len(noDoi) + len(noAuthor_withDoiTitle) + len(noYear_withDoiTitleAuthor)}")
print(database_refs)
print(f"No Doi: {len(noDoi)}")
print(f"No Titles: {len(noTitle_withDoi)}")
print(f"No Author: {len(noAuthor_withDoiTitle)}")
print(f"No Year: {len(noYear_withDoiTitleAuthor)}")
print(f"Duplicates Removed: {len(dups)}")

print("\n")
print("Saving deduplicate ris:")
with open(f"{OUT_DIR}allRefs.ris", "w") as outFile:
    for ref_ in raw_refs:
        for line_ in ref_:
            outFile.write(f"{line_}\n")
        outFile.write("\n")

i_ref = list(range(0, len(raw_refs)))
shuffle(i_ref)

n_refs = len(i_ref)
n_coScreen = 500
n_zar = round((n_refs-n_coScreen)/3)
n_sam = n_refs - (n_coScreen + n_zar)
print(f"Number to screen together: {n_coScreen}")
print(f"Number for primary reviewer: {n_sam}")
print(f"Number for secondary reviewer: {n_zar}")

def getRefs(raw_refs, indexes, start_i, n):
    if n is not None:
        indexes = indexes[start_i:n]
    else:
        indexes = indexes[start_i:]

    return [raw_refs[i] for i in indexes]

i = 0

with open(f"{OUT_DIR}coScreen.ris", "w") as outFile:
    for ref_ in getRefs(raw_refs, i_ref, i, n_coScreen):
        for line_ in ref_:
            outFile.write(f"{line_}\n")
        outFile.write("\n")
i += n_coScreen

with open(f"{OUT_DIR}secondaryReviewer.ris", "w") as outFile:
    for ref_ in getRefs(raw_refs, i_ref, i, n_zar):
        for line_ in ref_:
            outFile.write(f"{line_}\n")
        outFile.write("\n")
i += n_coScreen

with open(f"{OUT_DIR}primaryReviewer.ris", "w") as outFile:
    for ref_ in getRefs(raw_refs, i_ref, i, None): #All the rest
        for line_ in ref_:
            outFile.write(f"{line_}\n")
        outFile.write("\n")
i += n_coScreen

print("Finished")


