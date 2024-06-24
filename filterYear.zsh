# ris = proquest scopus webOfScience campbell cochrane epistemonikos ovidEbmr ovidEbmrEmbase
# csv = clinicalTrialsGov
# txt = grey healthEvidence pubmed
#
# Year field:
# 		proquest: DA (year) Y1 (date)
# 		scopus: PY (year) 
# 		webOfScience: PY (year)
# 		campbell: PY (year) DA (date) Y1 (date)
# 		cochrane: PY (year)
# 		epistemonikos: PY (year) DA (year)
# 		ovidEbmr: Y1 (f"{year}//") Y2 (unformatted date)
# 		ovidEbmrEmbase: Y1 (f"{year}//")
#
# 		clinicalTrialsGov: Start Date (Y-m-d)
#
# 		grey: 1 file per ref; new line per author; last author ends with (AUTHOR (YEAR))
# 		healthEvidence: ris-like format. Y1 (date Y/m/d)
# 		pubmed: ris-like format. DP (date e.g. "2019 Oct")

dirs_ris=(proquest scopus webOfScience campbell cochrane epistemonikos ovidEbmr ovidEbmrEmbase pubmed healthEvidence);
dirs_csv=(clinicalTrialsGov);
dirs_txt=(grey);

subdir_searches="searchOuts"

YearFiltLow_exclusive=2010;

echo -ne "\nRemoving non-utf-8 characters from healthEvidence (was causing issues).\n"
for file in $(ls "healthEvidence/${subdir_searches}");
do
    file="healthEvidence/${subdir_searches}/${file}"
    iconv -c -f utf-8 -t utf-8 $file > temp.txt && mv temp.txt $file
done

echo -ne "\nRunning ris filtering\nNote: 'Completed' denotes the number of references filtered through for the directory (not how many completed for a specific ris file).\nOutput file: ris with all references separated by a single new line. No new line after the last reference.\nclinicalTrialsGov and grey have not yet undergone this process."

for dir in ${dirs_ris[@]};
do
	echo -en "\n\n${dir}"
	i=0

	newFile="${dir}/${dir}_yearFilt_${YearFiltLow_exclusive}.ris"
	rm $newFile
	touch $newFile

	newFileRemoved="${dir}/${dir}_EXCLUDED_yearFilt_${YearFiltLow_exclusive}.ris"
	rm $newFileRemoved
	touch $newFileRemoved

	yearField="PY"
	if [ $dir = "ovidEbmr" ] || [ $dir = "ovidEbmrEmbase" ] || [ $dir = "healthEvidence" ];
	then
		yearField="Y1";
	fi;
	if [ $dir = "proquest" ];
	then
		yearField="DA";
	fi;
	if [ $dir = "pubmed" ];
	then
		yearField="DP";
	fi;

	for file in $(ls "${dir}/${subdir_searches}"); # | grep .ris);
	do
		file="${dir}/${subdir_searches}/${file}"
		echo -en "\n${file}\n"
		tempArr_item=();
		while IFS= read -r line;
		do
			#Add line to record if not empty
			#ensures length array>0 works
			if [[ ! -z $line && ! $line =~ "^[[:space:]]*$" ]];
			then
				tempArr_item+=$line;
			fi;

			if [[ (-z $line || $line =~ "^[[:space:]]*$") && ${#tempArr_item[@]} -gt 0 ]]; #some ris >1 blank line between refs, or leading blank line to file
			then
				year=$(for x in $tempArr_item[@]; do echo "${x}"; done | sed -n -e "/^$yearField/p" | sed -n -e 's/^.*\([0-9]\{4\}\).*$/\1/p')
				if [[ $year -gt $YearFiltLow_exclusive ]];
				then
					for x in $tempArr_item[@]; do echo "${x}"; done >> $newFile 
					echo "" >> $newFile
				else
					for x in $tempArr_item[@]; do echo "${x}"; done >> $newFileRemoved
					echo "" >> $newFileRemoved
				fi;
				
				tempArr_item=();
				i=$(( $i + 1 ))
				echo -en "\rCompleted: $i"
			fi;
		done < $file;

		#Same operation as above
		#Processes reference if end of file no blank line
		if [[ ${#tempArr_item[@]} -gt 0 ]];
		then
			year=$(for x in $tempArr_item[@]; do echo "${x}"; done | sed -n -e "/^$yearField/p" | sed -n -e 's/^.*\([0-9]\{4\}\).*$/\1/p')
			if [[ $year -gt $YearFiltLow_exclusive ]];
			then
				for x in $tempArr_item[@]; do echo "${x}"; done >> $newFile 
				echo "" >> $newFile
			else
				for x in $tempArr_item[@]; do echo "${x}"; done >> $newFileRemoved
				echo "" >> $newFileRemoved
			fi;
			tempArr_item=();
			i=$(( $i + 1 ))
			echo -en "\rCompleted: $i"
		fi;

	done;
done;


