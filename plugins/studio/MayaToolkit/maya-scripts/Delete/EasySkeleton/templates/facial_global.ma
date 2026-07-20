//Maya ASCII 2022 scene
//Name: facial_global.ma
//Last modified: Fri, Feb 07, 2025 02:10:49 PM
//Codeset: 1252
requires maya "2022";
requires "stereoCamera" "10.0";
requires "mtoa" "5.0.0.4";
currentUnit -l centimeter -a degree -t film;
fileInfo "application" "maya";
fileInfo "product" "Maya 2022";
fileInfo "version" "2022";
fileInfo "cutIdentifier" "202303271415-baa69b5798";
fileInfo "osv" "Windows 10 Home Single Language v2009 (Build: 26100)";
fileInfo "UUID" "7B3CB600-4A9D-8BDA-BDEF-A7A02C6E431E";
createNode transform -s -n "persp";
	rename -uid "547006B1-47E8-7D7B-55C6-90B5290DFD52";
	setAttr ".v" no;
	setAttr ".t" -type "double3" -17.147810979352883 9.8914378841133903 31.135960524299506 ;
	setAttr ".r" -type "double3" -1.5383527295443324 -390.59999999978896 0 ;
createNode camera -s -n "perspShape" -p "persp";
	rename -uid "61B36D5E-4F00-1A4F-A6DE-3FB3FA34183E";
	setAttr -k off ".v" no;
	setAttr ".fl" 34.999999999999993;
	setAttr ".coi" 37.942775386269872;
	setAttr ".imn" -type "string" "persp";
	setAttr ".den" -type "string" "persp_depth";
	setAttr ".man" -type "string" "persp_mask";
	setAttr ".tp" -type "double3" -0.96763655730260223 10.506553129376758 0 ;
	setAttr ".hc" -type "string" "viewSet -p %camera";
createNode transform -s -n "top";
	rename -uid "AB1CB06C-4D58-6699-FBCC-1EB25E00CD65";
	setAttr ".v" no;
	setAttr ".t" -type "double3" 0 1000.1 0 ;
	setAttr ".r" -type "double3" -90 0 0 ;
createNode camera -s -n "topShape" -p "top";
	rename -uid "34951CE3-4EC0-48A9-4609-4EA232DAC75D";
	setAttr -k off ".v" no;
	setAttr ".rnd" no;
	setAttr ".coi" 1000.1;
	setAttr ".ow" 30;
	setAttr ".imn" -type "string" "top";
	setAttr ".den" -type "string" "top_depth";
	setAttr ".man" -type "string" "top_mask";
	setAttr ".hc" -type "string" "viewSet -t %camera";
	setAttr ".o" yes;
	setAttr ".ai_translator" -type "string" "orthographic";
createNode transform -s -n "front";
	rename -uid "A10BA379-4D9C-7B16-5C05-B7A7B1722F18";
	setAttr ".v" no;
	setAttr ".t" -type "double3" 0 0 1000.1 ;
createNode camera -s -n "frontShape" -p "front";
	rename -uid "690F29EA-42D5-874E-78E3-A086CBFC5260";
	setAttr -k off ".v" no;
	setAttr ".rnd" no;
	setAttr ".coi" 1000.1;
	setAttr ".ow" 30;
	setAttr ".imn" -type "string" "front";
	setAttr ".den" -type "string" "front_depth";
	setAttr ".man" -type "string" "front_mask";
	setAttr ".hc" -type "string" "viewSet -f %camera";
	setAttr ".o" yes;
	setAttr ".ai_translator" -type "string" "orthographic";
createNode transform -s -n "side";
	rename -uid "7771A58B-4151-9D9D-D642-288A4830F6AD";
	setAttr ".v" no;
	setAttr ".t" -type "double3" 1000.1 0 0 ;
	setAttr ".r" -type "double3" 0 90 0 ;
createNode camera -s -n "sideShape" -p "side";
	rename -uid "B9F8F864-424F-AFF0-3155-B2A352897C61";
	setAttr -k off ".v" no;
	setAttr ".rnd" no;
	setAttr ".coi" 1000.1;
	setAttr ".ow" 30;
	setAttr ".imn" -type "string" "side";
	setAttr ".den" -type "string" "side_depth";
	setAttr ".man" -type "string" "side_mask";
	setAttr ".hc" -type "string" "viewSet -s %camera";
	setAttr ".o" yes;
	setAttr ".ai_translator" -type "string" "orthographic";
createNode transform -n "CharacterRig";
	rename -uid "5A0AC6ED-4D52-694D-AA10-5D83ABF3586E";
	setAttr -l on -k off ".tx";
	setAttr -l on -k off ".ty";
	setAttr -l on -k off ".tz";
	setAttr -l on -k off ".rx";
	setAttr -l on -k off ".ry";
	setAttr -l on -k off ".rz";
	setAttr -l on -k off ".sx";
	setAttr -l on -k off ".sy";
	setAttr -l on -k off ".sz";
createNode transform -n "Meshes" -p "CharacterRig";
	rename -uid "BCBE717A-4855-3305-99CE-58A185222A26";
	setAttr -l on -k off ".tx";
	setAttr -l on -k off ".ty";
	setAttr -l on -k off ".tz";
	setAttr -l on -k off ".rx";
	setAttr -l on -k off ".ry";
	setAttr -l on -k off ".rz";
	setAttr -l on -k off ".sx";
	setAttr -l on -k off ".sy";
	setAttr -l on -k off ".sz";
createNode transform -n "WorldCtrl" -p "CharacterRig";
	rename -uid "2F24E638-4C03-81B8-0AFE-6DB58B0A3D32";
	setAttr -l on -k off ".v";
createNode nurbsCurve -n "WorldCtrlShape" -p "WorldCtrl";
	rename -uid "825AB0F8-4283-0AFB-3015-C0BCFCF7B353";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovrgbf" yes;
	setAttr ".ovrgb" -type "float3" 0 0.0625 1 ;
	setAttr ".cc" -type "nurbsCurve" 
		1 4 0 no 3
		5 0 1 2 3 4
		5
		2.4657618590545058 0 -2.4657618590545058
		-2.4657618590545058 0 -2.4657618590545058
		-2.4657618590545058 0 2.4657618590545058
		2.4657618590545058 0 2.4657618590545058
		2.4657618590545058 0 -2.4657618590545058
		;
createNode transform -n "RootCtrl" -p "WorldCtrl";
	rename -uid "3F5650F5-49EA-C5DD-CC4F-74A4E5FEA3F0";
	setAttr -l on -k off ".v";
createNode nurbsCurve -n "RootCtrlShape" -p "RootCtrl";
	rename -uid "591C800A-4930-6106-216D-FAA731DABF83";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovrgbf" yes;
	setAttr ".ovrgb" -type "float3" 1 0.9375 0 ;
	setAttr ".cc" -type "nurbsCurve" 
		1 4 0 no 3
		5 0 1 2 3 4
		5
		1.9992453331948186 0 -1.9992453331948186
		-1.9992453331948186 0 -1.9992453331948186
		-1.9992453331948186 0 1.9992453331948186
		1.9992453331948186 0 1.9992453331948186
		1.9992453331948186 0 -1.9992453331948186
		;
createNode transform -n "rootLoc" -p "RootCtrl";
	rename -uid "DBCA42C4-455C-8B22-CCB3-4187EA6E7586";
	setAttr -l on -k off ".v" no;
	setAttr -l on -k off ".tx";
	setAttr -l on -k off ".ty";
	setAttr -l on -k off ".tz";
	setAttr -l on -k off ".rx";
	setAttr -l on -k off ".ry";
	setAttr -l on -k off ".rz";
	setAttr -l on -k off ".sx";
	setAttr -l on -k off ".sy";
	setAttr -l on -k off ".sz";
createNode locator -n "rootLocShape" -p "rootLoc";
	rename -uid "B4A4C413-40EB-DEB4-37D9-08AB1C01D9E3";
	setAttr -k off ".v";
createNode joint -n "LocalJoints" -p "CharacterRig";
	rename -uid "074FE19B-4490-1FFA-9B7A-51822914B08E";
	setAttr -l on -k off ".tx";
	setAttr -l on -k off ".ty";
	setAttr -l on -k off ".tz";
	setAttr -l on -k off ".rx";
	setAttr -l on -k off ".ry";
	setAttr -l on -k off ".rz";
	setAttr -l on -k off ".sx";
	setAttr -l on -k off ".sy";
	setAttr -l on -k off ".sz";
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".ssc" no;
	setAttr ".ds" 2;
	setAttr -l on -cb off ".radi" 0.5;
createNode joint -n "GlobalJoints" -p "CharacterRig";
	rename -uid "0B5B6485-4FFF-ABEC-FCCF-80B33775BF98";
	setAttr -l on -k off ".tx";
	setAttr -l on -k off ".ty";
	setAttr -l on -k off ".tz";
	setAttr -l on -k off ".rx";
	setAttr -l on -k off ".ry";
	setAttr -l on -k off ".rz";
	setAttr -l on -k off ".sx";
	setAttr -l on -k off ".sy";
	setAttr -l on -k off ".sz";
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".ssc" no;
	setAttr ".ds" 2;
	setAttr -l on -cb off ".radi" 0.5;
createNode joint -n "facial_base" -p "GlobalJoints";
	rename -uid "1AAE8157-4A69-D4F3-B608-A4BAE9A97846";
	setAttr ".t" -type "double3" 0 8.0354281273952015 -3.2200916790394705 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".ds" 3;
	setAttr ".radi" 0.5;
createNode joint -n "LFT_brow1" -p "facial_base";
	rename -uid "4F8BC46B-4CA6-C62F-A3BE-28890C5ED356";
	setAttr ".t" -type "double3" 1.2139480116101011 3.9267523984256787 3.2200916790394705 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".radi" 0.5;
createNode joint -n "LFT_brow2" -p "facial_base";
	rename -uid "59C6F8CD-496D-DE49-6F1B-05BEBCFDECD1";
	setAttr ".t" -type "double3" 2.0083538463429389 3.9267523984256787 3.2200916790394705 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".radi" 0.5;
createNode joint -n "LFT_brow3" -p "facial_base";
	rename -uid "F9ADA43D-4962-65B6-1326-C684C8FDA115";
	setAttr ".t" -type "double3" 2.7270531247160616 3.9267523984256787 3.2200916790394705 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".radi" 0.5;
createNode joint -n "CEN_brow" -p "facial_base";
	rename -uid "47FC4D5E-4A0A-3CD0-A6F4-C588E786455C";
	setAttr ".t" -type "double3" 0 3.9267523984256787 3.2200916790394705 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".radi" 0.5;
createNode joint -n "jaw" -p "facial_base";
	rename -uid "6113C27F-468A-0E5A-851E-65BB228D9B41";
	setAttr ".t" -type "double3" 0 -2.3669374548566715 1.4451427397923178 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".ds" 3;
	setAttr ".radi" 0.5;
createNode joint -n "mouthBase" -p "jaw";
	rename -uid "47688410-43E4-D014-B8F6-71BE29E20143";
	setAttr ".t" -type "double3" 0 0.54695459090901544 0.56230689941892242 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".ds" 3;
	setAttr ".radi" 0.5;
createNode joint -n "RGT_lipUp3" -p "mouthBase";
	rename -uid "3BC8193B-4083-F921-0648-D9A69CC5AD40";
	setAttr ".t" -type "double3" -2.02322 0.61424473655245482 1.8273040398282303 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".jo" -type "double3" -180 0 0 ;
	setAttr ".radi" 0.5;
createNode joint -n "RGT_lipUp2" -p "mouthBase";
	rename -uid "2F41F770-436A-BBDF-E7E5-65AD4C3748D5";
	setAttr ".t" -type "double3" -1.36563 0.61424473655245482 1.8273040398282303 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".jo" -type "double3" -180 0 0 ;
	setAttr ".radi" 0.5;
createNode joint -n "RGT_lipLow1" -p "mouthBase";
	rename -uid "494B9C37-4D89-219D-9E52-C388991E0ECC";
	setAttr ".t" -type "double3" -0.725858 -0.266625263447545 1.8273040398282303 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".jo" -type "double3" -180 0 0 ;
	setAttr ".radi" 0.5;
createNode joint -n "RGT_lipUp1" -p "mouthBase";
	rename -uid "2DFC79ED-4D28-8FB9-D007-F3BA74D34413";
	setAttr ".t" -type "double3" -0.725858 0.61424473655245482 1.8273040398282303 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".jo" -type "double3" -180 0 0 ;
	setAttr ".radi" 0.5;
createNode joint -n "RGT_lipLow2" -p "mouthBase";
	rename -uid "544A6105-48EE-ABBD-DE04-F8874E8ADE37";
	setAttr ".t" -type "double3" -1.36563 -0.266625263447545 1.8273040398282303 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".jo" -type "double3" -180 0 0 ;
	setAttr ".radi" 0.5;
createNode joint -n "RGT_lipCorner1" -p "mouthBase";
	rename -uid "E1EE031E-4F7E-F165-B880-A4B554B606D6";
	setAttr ".t" -type "double3" -2.65521 0.28034473655245495 1.8273040398282303 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".jo" -type "double3" -180 0 0 ;
	setAttr ".radi" 0.5;
createNode joint -n "RGT_lipLow3" -p "mouthBase";
	rename -uid "1FBF03AF-428A-67A9-C6FE-5782441C02BF";
	setAttr ".t" -type "double3" -2.02322 -0.266625263447545 1.8273040398282303 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".jo" -type "double3" -180 0 0 ;
	setAttr ".radi" 0.5;
createNode joint -n "CEN_lipUp" -p "mouthBase";
	rename -uid "F995ADB7-40DB-6B48-6D7B-2989B9431719";
	setAttr ".t" -type "double3" 0 0.61424092198191715 1.8273045108317723 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".radi" 0.5;
createNode joint -n "LFT_lipLow3" -p "mouthBase";
	rename -uid "FCB24670-4633-A1B2-C0C1-F59F0067B57E";
	setAttr ".t" -type "double3" 2.0232236755992963 -0.26662198354070821 1.8273045108317723 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".radi" 0.5;
createNode joint -n "LFT_lipLow1" -p "mouthBase";
	rename -uid "8BC811E2-4ADD-91C8-714F-81BBF7B18189";
	setAttr ".t" -type "double3" 0.7258583334876576 -0.26662198354070821 1.8273045108317723 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".radi" 0.5;
createNode joint -n "LFT_lipUp3" -p "mouthBase";
	rename -uid "DE694CC9-4638-1ACB-BF4A-D488C33CEE21";
	setAttr ".t" -type "double3" 2.0232236755992963 0.61424092198191715 1.8273045108317723 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".radi" 0.5;
createNode joint -n "LFT_lipUp2" -p "mouthBase";
	rename -uid "36E4F0D5-4018-3ED9-DBF4-EB927A69299F";
	setAttr ".t" -type "double3" 1.3656299882308047 0.61424092198191715 1.8273045108317723 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".radi" 0.5;
createNode joint -n "LFT_lipCorner1" -p "mouthBase";
	rename -uid "09E193E6-4869-DA07-FD54-2488B622A648";
	setAttr ".t" -type "double3" 2.6552136720024082 0.28034514435844837 1.8273045108317723 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".radi" 0.5;
createNode joint -n "LFT_lipLow2" -p "mouthBase";
	rename -uid "1742021C-4759-20DD-2450-6AA467EE7872";
	setAttr ".t" -type "double3" 1.3656299882308047 -0.26662198354070821 1.8273045108317723 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".radi" 0.5;
createNode joint -n "LFT_lipUp1" -p "mouthBase";
	rename -uid "21A188F7-4FFE-D4B1-384A-59B4724AEDC3";
	setAttr ".t" -type "double3" 0.7258583334876576 0.61424092198191715 1.8273045108317723 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".radi" 0.5;
createNode joint -n "CEN_lipLow" -p "mouthBase";
	rename -uid "78960A0E-4A21-3C56-FC8B-2884EF3D6006";
	setAttr ".t" -type "double3" 0 -0.26662198354070821 1.8273045108317723 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".radi" 0.5;
createNode joint -n "CEN_teethUp" -p "mouthBase";
	rename -uid "5A8C7FD9-4B5F-E807-DE9F-6BAF7C38FEA0";
	setAttr ".t" -type "double3" 0 0.65055553453398218 0.057019090160804753 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".radi" 0.5;
createNode joint -n "CEN_teethLow" -p "mouthBase";
	rename -uid "3187E807-435B-4C92-2C60-21B5478391EA";
	setAttr ".t" -type "double3" 0 -0.7207287252672252 0.057019090160804753 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".radi" 0.5;
createNode joint -n "tongue1" -p "jaw";
	rename -uid "3573B3D4-4C80-EB55-00D4-B3BE91E3D36C";
	setAttr ".t" -type "double3" 0 0.68154767341462463 -0.39345593266479817 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".radi" 0.5;
createNode joint -n "tongue2" -p "tongue1";
	rename -uid "4D3520B9-4FE5-B11B-9ADF-92AED2EB6C7C";
	setAttr ".t" -type "double3" 0 0 0.64983115549681081 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".radi" 0.5;
createNode joint -n "tongue3" -p "tongue2";
	rename -uid "CAAE50EC-4715-30BB-1988-D99FCDCA66D8";
	setAttr ".t" -type "double3" 0 0 0.50936188276840344 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".radi" 0.5;
createNode joint -n "tongue4" -p "tongue3";
	rename -uid "6374651A-4C24-A97E-2D0A-3CAEEB5B5F1C";
	setAttr ".t" -type "double3" 0 0 0.55932060162442299 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".radi" 0.5;
createNode joint -n "RGT_brow1" -p "facial_base";
	rename -uid "55B0BA74-4D2D-391D-9C9C-A487D329D4F7";
	setAttr ".t" -type "double3" -1.21395 3.9267718726047978 3.2200916790394705 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".jo" -type "double3" -180 0 0 ;
	setAttr ".radi" 0.5;
createNode joint -n "RGT_brow2" -p "facial_base";
	rename -uid "499BD634-4340-409C-B5AC-6BB1761F8BCD";
	setAttr ".t" -type "double3" -2.00835 3.9267718726047978 3.2200916790394705 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".jo" -type "double3" -180 0 0 ;
	setAttr ".radi" 0.5;
createNode joint -n "RGT_brow3" -p "facial_base";
	rename -uid "535AE39F-4F09-6A2F-E52C-5E8811B622B6";
	setAttr ".t" -type "double3" -2.72705 3.9267718726047978 3.2200916790394705 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".jo" -type "double3" -180 0 0 ;
	setAttr ".radi" 0.5;
createNode joint -n "LFT_eyeBall" -p "facial_base";
	rename -uid "4D3FEAC8-418B-5393-92DA-7D9737CE427D";
	setAttr ".t" -type "double3" 2.191899344019403 1.7080756782059563 0.70723263026970917 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".ds" 3;
	setAttr ".radi" 0.5;
createNode joint -n "LFT_eyeBallCtrlPiv" -p "LFT_eyeBall";
	rename -uid "78DEBF19-4927-3D7D-111D-C7A8DBD17F22";
	setAttr ".t" -type "double3" 4.4408920985006262e-16 -1.7763568394002505e-15 12.720468006940028 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".radi" 0.5;
createNode joint -n "RGT_eyeBall" -p "facial_base";
	rename -uid "B33E5A2B-44AA-3FA2-2FE8-0699F03295A5";
	setAttr ".t" -type "double3" -2.1919 1.7080718726047976 0.70723263026970917 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".jo" -type "double3" -180 0 0 ;
	setAttr ".ds" 3;
	setAttr ".radi" 0.5;
createNode joint -n "RGT_eyeBallCtrlPiv" -p "RGT_eyeBall";
	rename -uid "7D3A07AD-42E6-548C-0A27-158A75326FD2";
	setAttr ".t" -type "double3" 4.4408920985006262e-16 0 -12.72046515564991 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".radi" 0.5;
createNode joint -n "LFT_cheek" -p "facial_base";
	rename -uid "318C1B49-42E1-B850-482C-62ACAABC6F85";
	setAttr ".t" -type "double3" 2.1520476981909482 -0.18365782389449237 4.2546290105500226 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".radi" 0.5;
createNode joint -n "RGT_cheek" -p "facial_base";
	rename -uid "2C0402AE-4244-1936-B3DE-CDBD270D1347";
	setAttr ".t" -type "double3" -2.15205 -0.18365812739520138 4.2546316790394707 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".jo" -type "double3" -180 0 0 ;
	setAttr ".radi" 0.5;
createNode joint -n "LFT_eyeBallBase" -p "facial_base";
	rename -uid "9DDEAA99-46A5-9F23-10EB-80BE7015D254";
	setAttr ".t" -type "double3" 2.191899344019403 1.7080756782059563 1.9943062339909017 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".radi" 0.5;
createNode joint -n "LFT_eyelidOuterCtrlGuide" -p "LFT_eyeBallBase";
	rename -uid "AF110E84-4A27-0C79-9406-899943C08F8D";
	setAttr ".t" -type "double3" 0.63832826942969367 0.011500123537025786 2.0306585087393008 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".radi" 0.5;
createNode joint -n "LFT_eyelidInnerCtrlGuide" -p "LFT_eyeBallBase";
	rename -uid "8EC1F063-446E-B5DE-E92B-0E8124644D21";
	setAttr ".t" -type "double3" -1.3947453346772094 0.011500123537025786 2.0306585087393008 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".jo" -type "double3" -180 0 0 ;
	setAttr ".radi" 0.5;
createNode joint -n "LFT_eyelidLowCtrlGuide" -p "LFT_eyeBallBase";
	rename -uid "E4D6D629-48CC-A8D9-F48F-E28A3E5AC46A";
	setAttr ".t" -type "double3" -0.38853684728172677 -0.91261791845516171 2.0306585087393008 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".jo" -type "double3" -180 0 0 ;
	setAttr ".radi" 0.5;
createNode joint -n "LFT_eyelidUpCtrlGuide" -p "LFT_eyeBallBase";
	rename -uid "4583AAE6-46BE-C39A-679B-EFA96B5B78BD";
	setAttr ".t" -type "double3" -0.38853684728172655 0.99544120172306094 2.0306585087393008 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".jo" -type "double3" -180 0 0 ;
	setAttr ".radi" 0.5;
createNode joint -n "LFT_eyelidUp1" -p "LFT_eyeBallBase";
	rename -uid "9E2F87FA-4CF2-F0BC-EF8D-FF94A47CD911";
	setAttr ".t" -type "double3" -1.3947453105435808 0.01150043197223205 1.2257854450485688 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".jo" -type "double3" -180 0 0 ;
	setAttr ".radi" 0.5;
createNode joint -n "LFT_eyelidUp3" -p "LFT_eyeBallBase";
	rename -uid "16E6D57D-4C4A-AB44-7819-30A1F5663105";
	setAttr ".t" -type "double3" -0.38853684728172611 0.99544094775364478 1.2257854450485688 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".jo" -type "double3" -180 0 0 ;
	setAttr ".radi" 0.5;
createNode joint -n "LFT_eyelidUp2" -p "LFT_eyeBallBase";
	rename -uid "F1BE1A88-47A4-1B70-101A-A3938FC420E5";
	setAttr ".t" -type "double3" -1.0922416468378144 0.71236843899469449 1.2257854450485688 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".jo" -type "double3" -180 0 0 ;
	setAttr ".radi" 0.5;
createNode joint -n "LFT_eyelidUp5" -p "LFT_eyeBallBase";
	rename -uid "85FC9463-4CC6-0B25-8A3B-60B832D48F50";
	setAttr ".t" -type "double3" 0.63832832601148226 0.011500865120963155 1.2257854450485688 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".jo" -type "double3" -180 0 0 ;
	setAttr ".radi" 0.5;
createNode joint -n "LFT_eyelidLow1" -p "LFT_eyeBallBase";
	rename -uid "489887A7-4294-903E-0A66-E99A574A76BB";
	setAttr ".t" -type "double3" -1.0922416468378144 -0.52195966608058697 1.2257854450485688 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".jo" -type "double3" -180 0 0 ;
	setAttr ".radi" 0.5;
createNode joint -n "LFT_eyelidLow2" -p "LFT_eyeBallBase";
	rename -uid "75A29A25-49C3-0029-9B69-F1865A9C72D7";
	setAttr ".t" -type "double3" -0.38853684728172611 -0.91261813677525438 1.2257854450485688 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".jo" -type "double3" -180 0 0 ;
	setAttr ".radi" 0.5;
createNode joint -n "LFT_eyelidLow3" -p "LFT_eyeBallBase";
	rename -uid "43568FFE-4A05-7EB4-22E8-C087DF928A77";
	setAttr ".t" -type "double3" 0.28023606699400005 -0.54161158188147773 1.2257854450485688 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".jo" -type "double3" -180 0 0 ;
	setAttr ".radi" 0.5;
createNode joint -n "LFT_eyelidUp4" -p "LFT_eyeBallBase";
	rename -uid "972546E6-464A-B03C-D937-E39E82B00391";
	setAttr ".t" -type "double3" 0.28023606699400005 0.69271652319380372 1.2257854450485688 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".jo" -type "double3" -180 0 0 ;
	setAttr ".radi" 0.5;
createNode joint -n "RGT_eyeBallBase" -p "facial_base";
	rename -uid "02749004-4A05-1E7F-253E-19B8B8394B6C";
	setAttr ".t" -type "double3" -2.1919 1.7080718726047976 1.9943016790394705 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".jo" -type "double3" -180 0 0 ;
	setAttr ".radi" 0.5;
createNode joint -n "RGT_eyelidOuterCtrlGuide" -p "RGT_eyeBallBase";
	rename -uid "783D63C6-4E94-EA1C-7FF0-CABA8EE0AEA3";
	setAttr ".t" -type "double3" -0.63832999999999984 -0.01150000000000162 -2.0306629999999997 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".radi" 0.5;
createNode joint -n "RGT_eyelidInnerCtrlGuide" -p "RGT_eyeBallBase";
	rename -uid "A2E7E76C-4CCD-8FCC-9B91-66B38DBDCCD9";
	setAttr ".t" -type "double3" 1.394746 -0.01150000000000162 -2.0306629999999997 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".jo" -type "double3" -180 0 0 ;
	setAttr ".radi" 0.5;
createNode joint -n "RGT_eyelidLowCtrlGuide" -p "RGT_eyeBallBase";
	rename -uid "48910BBB-41AF-B167-8551-F983DD8AE74D";
	setAttr ".t" -type "double3" 0.38853999999999989 0.91260999999999903 -2.0306629999999997 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".jo" -type "double3" -180 0 0 ;
	setAttr ".radi" 0.5;
createNode joint -n "RGT_eyelidUpCtrlGuide" -p "RGT_eyeBallBase";
	rename -uid "43FE8829-4D88-1E2A-7E9B-388769B77F3F";
	setAttr ".t" -type "double3" 0.38853999999999989 -0.99540000000000006 -2.0306629999999997 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".jo" -type "double3" -180 0 0 ;
	setAttr ".radi" 0.5;
createNode joint -n "RGT_eyelidUp1" -p "RGT_eyeBallBase";
	rename -uid "ABAFF4A0-4C29-3599-0E9A-04A46DD489EE";
	setAttr ".t" -type "double3" 1.394746 -0.01150000000000162 -1.22579 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".jo" -type "double3" -180 0 0 ;
	setAttr ".radi" 0.5;
createNode joint -n "RGT_eyelidUp3" -p "RGT_eyeBallBase";
	rename -uid "DC96BC36-4082-96F7-8A3C-F8811FAEB5FA";
	setAttr ".t" -type "double3" 0.38853999999999989 -0.99540000000000006 -1.2257899999999997 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".jo" -type "double3" -180 0 0 ;
	setAttr ".radi" 0.5;
createNode joint -n "RGT_eyelidUp2" -p "RGT_eyeBallBase";
	rename -uid "E87BB1DE-4B54-8CF3-612C-0BB850E1AEAA";
	setAttr ".t" -type "double3" 1.0922399999999999 -0.71240000000000059 -1.2257899999999997 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".jo" -type "double3" -180 0 0 ;
	setAttr ".radi" 0.5;
createNode joint -n "RGT_eyelidUp5" -p "RGT_eyeBallBase";
	rename -uid "B56066A7-42C6-9172-3E4C-43870A981AB1";
	setAttr ".t" -type "double3" -0.63832999999999984 -0.01150000000000162 -1.22579 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".jo" -type "double3" -180 0 0 ;
	setAttr ".radi" 0.5;
createNode joint -n "RGT_eyelidLow1" -p "RGT_eyeBallBase";
	rename -uid "7BE6A947-4F2D-357A-5FB2-3E907F4C56FE";
	setAttr ".t" -type "double3" 1.0922399999999999 0.52196 -1.22579 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".jo" -type "double3" -180 0 0 ;
	setAttr ".radi" 0.5;
createNode joint -n "RGT_eyelidLow2" -p "RGT_eyeBallBase";
	rename -uid "53978E7E-4236-4222-DD38-57A69D4BAEE3";
	setAttr ".t" -type "double3" 0.38853999999999989 0.91260999999999903 -1.22579 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".jo" -type "double3" -180 0 0 ;
	setAttr ".radi" 0.5;
createNode joint -n "RGT_eyelidLow3" -p "RGT_eyeBallBase";
	rename -uid "A846B298-4998-72A9-0956-7A99C5FB2074";
	setAttr ".t" -type "double3" -0.28024000000000004 0.54160999999999859 -1.22579 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".jo" -type "double3" -180 0 0 ;
	setAttr ".radi" 0.5;
createNode joint -n "RGT_eyelidUp4" -p "RGT_eyeBallBase";
	rename -uid "9CFE3895-4D45-1986-4FD1-F38822733C2E";
	setAttr ".t" -type "double3" -0.28024000000000004 -0.69270000000000032 -1.2257899999999997 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".jo" -type "double3" -180 0 0 ;
	setAttr ".radi" 0.5;
createNode joint -n "nose_base" -p "facial_base";
	rename -uid "50A87FBE-486A-BFDB-7890-19959F81C4E2";
	setAttr ".t" -type "double3" 0 -0.18365782389449237 4.2546290105500226 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".radi" 0.5;
createNode joint -n "nose_tip" -p "facial_base";
	rename -uid "079EA1B6-450D-30E3-9050-E187FE6416EC";
	setAttr ".t" -type "double3" 0 -0.18365782389449237 4.9718984391526035 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".radi" 0.5;
createNode joint -n "LFT_nose_wing" -p "facial_base";
	rename -uid "FB57B333-4C8A-35EF-D67B-C0B565B53426";
	setAttr ".t" -type "double3" 0.61750806289901172 -0.18365782389449237 4.2546289944081224 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".radi" 0.5;
createNode joint -n "RGT_nose_wing" -p "facial_base";
	rename -uid "FC030B88-4D2D-4001-467B-79ABD497B168";
	setAttr ".t" -type "double3" -0.617508 -0.18365812739520138 4.2546316790394707 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".jo" -type "double3" -180 0 0 ;
	setAttr ".radi" 0.5;
createNode joint -n "LFT_ear1" -p "facial_base";
	rename -uid "245BF6AD-4A69-589C-2EA0-35A4706C5BB5";
	setAttr ".t" -type "double3" 3.5409996609958321 1.3752720838825834 1.5769199767457831 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".ds" 3;
	setAttr ".radi" 0.5;
createNode joint -n "LFT_ear2" -p "LFT_ear1";
	rename -uid "38D095B2-482C-FBF6-4222-BE84C2C9DC96";
	setAttr ".t" -type "double3" 0 0 -0.47322306035026651 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".ds" 3;
	setAttr ".radi" 0.5;
createNode joint -n "RGT_ear1" -p "facial_base";
	rename -uid "12BEB745-4213-E5CD-5376-CE95688F7F93";
	setAttr ".t" -type "double3" -3.541 1.3752718726047988 1.5769216790394704 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".jo" -type "double3" -180 0 0 ;
	setAttr ".ds" 3;
	setAttr ".radi" 0.5;
createNode joint -n "RGT_ear2" -p "RGT_ear1";
	rename -uid "0D4C81E5-4A4F-80A6-DC19-D28DAD46B771";
	setAttr ".t" -type "double3" 0 0 0.4732200000000002 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".ds" 3;
	setAttr ".radi" 0.5;
createNode transform -n "AutoRig" -p "CharacterRig";
	rename -uid "2EEF53D4-4B3F-C00E-8A2E-04881F88A76B";
	setAttr -l on -k off ".tx";
	setAttr -l on -k off ".ty";
	setAttr -l on -k off ".tz";
	setAttr -l on -k off ".rx";
	setAttr -l on -k off ".ry";
	setAttr -l on -k off ".rz";
	setAttr -l on -k off ".sx";
	setAttr -l on -k off ".sy";
	setAttr -l on -k off ".sz";
createNode transform -n "Others" -p "CharacterRig";
	rename -uid "B63180F9-481D-A64A-02DA-BE8561F6D3E8";
	setAttr -l on -k off ".tx";
	setAttr -l on -k off ".ty";
	setAttr -l on -k off ".tz";
	setAttr -l on -k off ".rx";
	setAttr -l on -k off ".ry";
	setAttr -l on -k off ".rz";
	setAttr -l on -k off ".sx";
	setAttr -l on -k off ".sy";
	setAttr -l on -k off ".sz";
createNode transform -n "LocalJointsBackup" -p "Others";
	rename -uid "1F6C161A-4BAA-5B64-4F69-A2BF36734F7B";
	setAttr ".v" no;
createNode transform -n "GlobalJointsBackup" -p "Others";
	rename -uid "C409E5AA-4B88-A882-CA55-43A021810E2B";
	setAttr ".v" no;
createNode joint -n "LFT_brow1_Backup" -p "GlobalJointsBackup";
	rename -uid "00FD4ED6-44DB-941C-A0A6-F2B2DC1CE80C";
	setAttr ".t" -type "double3" 2.0074646451982963 11.08291540388881 0 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".radi" 0.5;
createNode joint -n "LFT_brow2_Backup" -p "GlobalJointsBackup";
	rename -uid "9C415D3A-4F3F-8C73-7C09-B3BA01D0B670";
	setAttr ".t" -type "double3" 3.1238381762078316 11.08291540388881 0 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".radi" 0.5;
createNode joint -n "LFT_brow3_Backup" -p "GlobalJointsBackup";
	rename -uid "ED6DD7CE-4A87-180C-26FC-B898A6218B70";
	setAttr ".t" -type "double3" 4.2857832800555578 11.08291540388881 0 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".radi" 0.5;
createNode joint -n "RGT_brow1_Backup" -p "GlobalJointsBackup";
	rename -uid "6BDD8AE0-475B-87F3-BBA2-6DAA94959952";
	setAttr ".t" -type "double3" -2.00746 11.0829 0 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".jo" -type "double3" -180 0 0 ;
	setAttr ".radi" 0.5;
createNode joint -n "RGT_brow2_Backup" -p "GlobalJointsBackup";
	rename -uid "64CCBD8A-45C8-1E3F-8A2B-CC8FA5818EC7";
	setAttr ".t" -type "double3" -3.12384 11.0829 0 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".jo" -type "double3" -180 0 0 ;
	setAttr ".radi" 0.5;
createNode joint -n "RGT_brow3_Backup" -p "GlobalJointsBackup";
	rename -uid "9959AB94-4931-4B8A-CB06-D1A29BAC3B9B";
	setAttr ".t" -type "double3" -4.28578 11.0829 0 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".jo" -type "double3" -180 0 0 ;
	setAttr ".radi" 0.5;
createNode joint -n "CEN_brow_Backup" -p "GlobalJointsBackup";
	rename -uid "636B9BC3-4CCE-D85B-0E13-5F83CDA4115C";
	setAttr ".t" -type "double3" 0 11.08291540388881 0 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".radi" 0.5;
createNode joint -n "RGT_lipUp3_Backup" -p "GlobalJointsBackup";
	rename -uid "1A86A40F-4038-B6A8-964D-F48FA3490170";
	setAttr ".t" -type "double3" -2.02322 6.82969 0.614662 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".jo" -type "double3" -180 0 0 ;
	setAttr ".radi" 0.5;
createNode joint -n "RGT_lipUp2_Backup" -p "GlobalJointsBackup";
	rename -uid "B744385F-4F48-47CF-C2C3-7692D4350BC2";
	setAttr ".t" -type "double3" -1.36563 6.82969 0.614662 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".jo" -type "double3" -180 0 0 ;
	setAttr ".radi" 0.5;
createNode joint -n "RGT_lipLow1_Backup" -p "GlobalJointsBackup";
	rename -uid "4D8394AA-4A13-7A36-9E42-67B644575A17";
	setAttr ".t" -type "double3" -0.725858 5.94882 0.614662 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".jo" -type "double3" -180 0 0 ;
	setAttr ".radi" 0.5;
createNode joint -n "RGT_lipUp1_Backup" -p "GlobalJointsBackup";
	rename -uid "29F97FFC-4757-1430-AF80-35970448088E";
	setAttr ".t" -type "double3" -0.725858 6.82969 0.614662 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".jo" -type "double3" -180 0 0 ;
	setAttr ".radi" 0.5;
createNode joint -n "RGT_lipLow2_Backup" -p "GlobalJointsBackup";
	rename -uid "B2646E66-4116-31A7-5385-1495280BDF82";
	setAttr ".t" -type "double3" -1.36563 5.94882 0.614662 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".jo" -type "double3" -180 0 0 ;
	setAttr ".radi" 0.5;
createNode joint -n "RGT_lipCorner1_Backup" -p "GlobalJointsBackup";
	rename -uid "5F15920B-452E-F60A-7DAA-E9BAA3CE428E";
	setAttr ".t" -type "double3" -2.65521 6.49579 0.614662 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".jo" -type "double3" -180 0 0 ;
	setAttr ".radi" 0.5;
createNode joint -n "RGT_lipLow3_Backup" -p "GlobalJointsBackup";
	rename -uid "4551DF6B-4B99-1AF7-B463-458632CEF7E9";
	setAttr ".t" -type "double3" -2.02322 5.94882 0.614662 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".jo" -type "double3" -180 0 0 ;
	setAttr ".radi" 0.5;
createNode joint -n "CEN_lipUp_Backup" -p "GlobalJointsBackup";
	rename -uid "EF6B26F3-4312-C2F7-373C-9593CCCB8849";
	setAttr ".t" -type "double3" 0 6.8296861854294626 0.61466247100354199 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".radi" 0.5;
createNode joint -n "LFT_lipLow3_Backup" -p "GlobalJointsBackup";
	rename -uid "6CC95D29-4F65-7CCD-9CCE-4CB778D1E7C0";
	setAttr ".t" -type "double3" 2.0232236755992963 5.9488232799068372 0.61466247100354199 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".radi" 0.5;
createNode joint -n "LFT_lipLow1_Backup" -p "GlobalJointsBackup";
	rename -uid "999EB455-4A32-E8DA-F868-A7BB6242836F";
	setAttr ".t" -type "double3" 0.7258583334876576 5.9488232799068372 0.61466247100354199 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".radi" 0.5;
createNode joint -n "LFT_lipUp3_Backup" -p "GlobalJointsBackup";
	rename -uid "26CD5A93-467F-B772-5086-998FA27C1383";
	setAttr ".t" -type "double3" 2.0232236755992963 6.8296861854294626 0.61466247100354199 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".radi" 0.5;
createNode joint -n "LFT_lipUp2_Backup" -p "GlobalJointsBackup";
	rename -uid "B91E0186-4994-B6B7-BFE4-BAA9E541A57C";
	setAttr ".t" -type "double3" 1.3656299882308047 6.8296861854294626 0.61466247100354199 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".radi" 0.5;
createNode joint -n "LFT_lipCorner1_Backup" -p "GlobalJointsBackup";
	rename -uid "0FFC237E-47FD-84B7-4F9A-DF81FB134391";
	setAttr ".t" -type "double3" 2.6552136720024082 6.4957904078059938 0.61466247100354199 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".radi" 0.5;
createNode joint -n "LFT_lipLow2_Backup" -p "GlobalJointsBackup";
	rename -uid "F493ED4F-4408-D49F-B968-0D9077A9572A";
	setAttr ".t" -type "double3" 1.3656299882308047 5.9488232799068372 0.61466247100354199 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".radi" 0.5;
createNode joint -n "LFT_lipUp1_Backup" -p "GlobalJointsBackup";
	rename -uid "CA31EE8B-4BE5-9BAB-A23D-0091B046E72B";
	setAttr ".t" -type "double3" 0.7258583334876576 6.8296861854294626 0.61466247100354199 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".radi" 0.5;
createNode joint -n "CEN_lipLow_Backup" -p "GlobalJointsBackup";
	rename -uid "FF9FCA1C-4546-F632-2118-598A4C1F181C";
	setAttr ".t" -type "double3" 0 5.9488232799068372 0.61466247100354199 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".radi" 0.5;
createNode joint -n "CEN_teethUp_Backup" -p "GlobalJointsBackup";
	rename -uid "E70FEE91-4AA7-0F25-6719-678C3D3B1ABB";
	setAttr ".t" -type "double3" 0 6.8660007979815276 -1.1556229496674255 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".radi" 0.5;
createNode joint -n "CEN_teethLow_Backup" -p "GlobalJointsBackup";
	rename -uid "D97716E2-42BF-57F2-E010-A48BF2C835F4";
	setAttr ".t" -type "double3" 0 5.4947165381803202 -1.1556229496674255 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".radi" 0.5;
createNode joint -n "mouthBase_Backup" -p "GlobalJointsBackup";
	rename -uid "915087E2-4E99-662F-D7E1-C988284CEF2F";
	setAttr ".t" -type "double3" 0 6.2154452634475454 -1.2126420398282303 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".radi" 0.5;
createNode joint -n "tongue4_Backup" -p "GlobalJointsBackup";
	rename -uid "A2DF53AD-4B31-C472-02A7-7D8D9B5EB762";
	setAttr ".t" -type "double3" 0 6.3500383459531546 -0.44989123202231363 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".radi" 0.5;
createNode joint -n "tongue3_Backup" -p "GlobalJointsBackup";
	rename -uid "97ADCA49-442E-7880-1894-0BAA24AB0782";
	setAttr ".t" -type "double3" 0 6.3500383459531546 -1.0092118336467366 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".radi" 0.5;
createNode joint -n "tongue2_Backup" -p "GlobalJointsBackup";
	rename -uid "3204D497-444A-1639-9F94-7F8B102FA97D";
	setAttr ".t" -type "double3" 0 6.3500383459531546 -1.5185737164151401 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".radi" 0.5;
createNode joint -n "tongue1_Backup" -p "GlobalJointsBackup";
	rename -uid "D38A8E2A-493F-686C-B9D3-D18144AD8014";
	setAttr ".t" -type "double3" 0 6.3500383459531546 -2.1684048719119509 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".radi" 0.5;
createNode joint -n "jaw_Backup" -p "GlobalJointsBackup";
	rename -uid "3A18B572-436B-B2EF-2963-54B1CB297AF5";
	setAttr ".t" -type "double3" 0 5.66849067253853 -1.7749489392471527 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".radi" 0.5;
createNode transform -n "ControllerBackup" -p "Others";
	rename -uid "C79C83BB-4966-0D37-57BC-0A87412EC6FD";
	setAttr ".v" no;
createNode transform -n "ControllerReference" -p "Others";
	rename -uid "C5CF005D-44A7-BE51-4E06-E28FC04ED21B";
	setAttr ".v" no;
createNode transform -n "TwoD_Square" -p "ControllerReference";
	rename -uid "8E91CD69-4B8A-C00A-B734-86963D40DD77";
createNode nurbsCurve -n "TwoD_SquareShape" -p "TwoD_Square";
	rename -uid "E9EDF66A-4617-C381-0F21-B393EA2FD061";
	setAttr -k off ".v";
	setAttr ".cc" -type "nurbsCurve" 
		1 4 0 no 3
		5 0 1 2 3 4
		5
		1 0 -1
		-1 0 -1
		-1 0 1
		1 0 1
		1 0 -1
		;
createNode transform -n "TwoD_Triangle" -p "ControllerReference";
	rename -uid "666866AE-40C4-104E-FDBF-C0A6D7AF05E9";
createNode nurbsCurve -n "TwoD_TriangleShape" -p "TwoD_Triangle";
	rename -uid "98CB5730-4751-A8CC-5A29-BA86895638E2";
	setAttr -k off ".v";
	setAttr ".cc" -type "nurbsCurve" 
		1 3 0 no 3
		4 0 1 2 3
		4
		-0.74263186877646659 0 -0.99141935077929189
		-0.74263186877646659 0 0.99141935077929189
		0.97450927334304804 0 0
		-0.74263186877646659 0 -0.99141935077929189
		;
createNode transform -n "TwoD_Hexagon" -p "ControllerReference";
	rename -uid "D986D11B-467F-9776-D64D-6C896D2CF0AE";
createNode nurbsCurve -n "TwoD_HexagonShape" -p "TwoD_Hexagon";
	rename -uid "215DA4C6-4BFD-7DA8-CD06-058F88F83F2D";
	setAttr -k off ".v";
	setAttr ".cc" -type "nurbsCurve" 
		1 6 0 no 3
		7 0 1 2 3 4 5 6
		7
		-1 0 0
		-0.5 0 -0.86599999999999999
		0.5 0 -0.86599999999999999
		1 0 0
		0.5 0 0.86599999999999999
		-0.5 0 0.86599999999999999
		-1 0 0
		;
createNode transform -n "TwoD_HalfCircle" -p "ControllerReference";
	rename -uid "151994A1-4464-9666-B964-E092DC58BBD6";
createNode nurbsCurve -n "TwoD_HalfCircleShape" -p "TwoD_HalfCircle";
	rename -uid "D28A0A3D-4050-2E96-6ACB-35A3C47B4942";
	setAttr -k off ".v";
	setAttr ".cc" -type "nurbsCurve" 
		3 4 0 no 3
		9 0 0 0 1 2 3 4 4 4
		7
		0 0 -1
		-0.26119999999999999 0 -1
		-0.78359999999999996 0 -0.78359999999999996
		-1.1082000000000001 0 0
		-0.78359999999999996 0 0.78359999999999996
		-0.26119999999999999 0 1
		0 0 1
		;
createNode transform -n "TwoD_Circle" -p "ControllerReference";
	rename -uid "7174BFA6-4254-2A6A-9BCE-7390A32C76DC";
createNode nurbsCurve -n "TwoD_CircleShape" -p "TwoD_Circle";
	rename -uid "AFF83916-469F-476A-852D-8EBA16EE1407";
	setAttr -k off ".v";
	setAttr ".cc" -type "nurbsCurve" 
		3 8 2 no 3
		13 -2 -1 0 1 2 3 4 5 6 7 8 9 10
		11
		0.78361162489122449 4.7982373409884731e-17 -0.7836116248912246
		6.7857323231109122e-17 6.7857323231109122e-17 -1.1081941875543877
		-0.78361162489122449 4.7982373409884719e-17 -0.78361162489122438
		-1.1081941875543881 3.5177356190060272e-33 -5.7448982375248304e-17
		-0.78361162489122449 -4.7982373409884725e-17 0.78361162489122449
		-1.1100856969603225e-16 -6.7857323231109171e-17 1.1081941875543884
		0.78361162489122449 -4.7982373409884719e-17 0.78361162489122438
		1.1081941875543881 -9.2536792101100989e-33 1.511240500779959e-16
		0.78361162489122449 4.7982373409884731e-17 -0.7836116248912246
		6.7857323231109122e-17 6.7857323231109122e-17 -1.1081941875543877
		-0.78361162489122449 4.7982373409884719e-17 -0.78361162489122438
		;
createNode transform -n "Extra_Pointer3" -p "ControllerReference";
	rename -uid "27E54BCE-4FE9-F82D-E4BB-18ADD528FB1A";
createNode nurbsCurve -n "Extra_Pointer3Shape" -p "Extra_Pointer3";
	rename -uid "04DD4C60-43BF-F5CF-4FFF-9F87347021C9";
	setAttr -k off ".v";
	setAttr ".cc" -type "nurbsCurve" 
		1 29 0 no 3
		30 0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27
		 28 29
		30
		0.76639999999999997 -3.4034997042908798e-16 0
		0.76639999999999997 -3.4034997042908798e-16 0.27110000000000001
		1.3086 -5.8113514000979193e-16 0
		0.76639999999999997 -3.4034997042908798e-16 -0.27110000000000001
		0.76639999999999997 -3.4034997042908798e-16 0
		0.24179999999999999 -1.0738077094174513e-16 0
		0.23350000000000001 -1.0369483049998963e-16 -0.061699999999999998
		0.20960000000000001 -9.3081098384573128e-17 -0.1192
		0.1719 -7.6338935173225762e-17 -0.16880000000000001
		0.12239999999999999 -5.4356519285647662e-17 -0.20649999999999999
		0.064799999999999996 -2.8776980798284056e-17 -0.2303
		0.0030999999999999999 -1.3766765505351941e-18 -0.2387
		-0.058599999999999999 2.6023627697213669e-17 -0.2303
		-0.11609999999999999 5.1558757263592267e-17 -0.20649999999999999
		-0.16569999999999999 7.3585582072155369e-17 -0.16880000000000001
		-0.2034 9.0327745283502735e-17 -0.1192
		-0.22720000000000001 1.0089706847793423e-16 -0.061699999999999998
		-0.2356 1.0462741784067475e-16 0
		-0.22720000000000001 1.0089706847793423e-16 0.061699999999999998
		-0.2034 9.0327745283502735e-17 0.1192
		-0.16569999999999999 7.3585582072155369e-17 0.16880000000000001
		-0.11609999999999999 5.1558757263592267e-17 0.20649999999999999
		-0.058599999999999999 2.6023627697213669e-17 0.2303
		0.0030999999999999999 -1.3766765505351941e-18 0.2387
		0.064799999999999996 -2.8776980798284056e-17 0.2303
		0.12239999999999999 -5.4356519285647662e-17 0.20649999999999999
		0.1719 -7.6338935173225762e-17 0.16880000000000001
		0.20960000000000001 -9.3081098384573128e-17 0.1192
		0.23350000000000001 -1.0369483049998963e-16 0.061699999999999998
		0.24179999999999999 -1.0738077094174513e-16 0
		;
createNode transform -n "Extra_Pointer2" -p "ControllerReference";
	rename -uid "1336233F-4A62-4434-B36E-599CEABC160C";
createNode nurbsCurve -n "Extra_Pointer2Shape" -p "Extra_Pointer2";
	rename -uid "55F6F594-4641-FAE9-AB20-58B095A7CACB";
	setAttr -k off ".v";
	setAttr ".cc" -type "nurbsCurve" 
		1 25 0 no 3
		26 0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25
		26
		0.70750000000000002 -3.1419311596891931e-16 0
		0.71830000000000005 -3.189892794353e-16 0.080199999999999994
		0.74929999999999997 -3.327560449406519e-16 0.15490000000000001
		0.79830000000000001 -3.5451641622330499e-16 0.21920000000000001
		0.86260000000000003 -3.8307135241666403e-16 0.26819999999999999
		0.93740000000000001 -4.162892253134487e-16 0.29920000000000002
		1.0175000000000001 -4.5186077102243874e-16 0.31
		1.0976999999999999 -4.8747672565241369e-16 0.29920000000000002
		1.1724000000000001 -5.2065018962821346e-16 0.26819999999999999
		1.2366999999999999 -5.492051258215724e-16 0.21920000000000001
		1.2857000000000001 -5.7096549710422553e-16 0.15490000000000001
		1.3167 -5.8473226260957744e-16 0.080199999999999994
		1.3274999999999999 -5.8952842607595808e-16 0
		1.3167 -5.8473226260957744e-16 -0.080199999999999994
		1.2857000000000001 -5.7096549710422553e-16 -0.15490000000000001
		1.2366999999999999 -5.492051258215724e-16 -0.21920000000000001
		1.1724000000000001 -5.2065018962821346e-16 -0.26819999999999999
		1.0976999999999999 -4.8747672565241369e-16 -0.29920000000000002
		1.0175000000000001 -4.5186077102243874e-16 -0.31
		0.93740000000000001 -4.162892253134487e-16 -0.29920000000000002
		0.86260000000000003 -3.8307135241666403e-16 -0.26819999999999999
		0.79830000000000001 -3.5451641622330499e-16 -0.21920000000000001
		0.74929999999999997 -3.327560449406519e-16 -0.15490000000000001
		0.71830000000000005 -3.189892794353e-16 -0.080199999999999994
		0.70750000000000002 -3.1419311596891931e-16 0
		0.0066 -2.9309887850104133e-18 0
		;
createNode transform -n "Extra_Pointer1" -p "ControllerReference";
	rename -uid "2DA8064F-4713-84CC-46C1-C6AD46A09E13";
createNode nurbsCurve -n "Extra_Pointer1Shape" -p "Extra_Pointer1";
	rename -uid "432A9CB6-432D-6B2F-930E-AC9C0EDABBBF";
	setAttr -k off ".v";
	setAttr ".cc" -type "nurbsCurve" 
		1 14 0 no 3
		15 0 1 2 3 4 5 6 7 8 9 10 11 12 13 14
		15
		0 0 0
		0.67197694083532789 0 -9.7754656704855059e-16
		0.77038796382066133 0 -0.23757744743233128
		1.0079654112529914 0 -0.33598847041766539
		1.2455428586853217 0 -0.23757744743233197
		1.3439538816706558 0 -1.9550931340971012e-15
		1.2455428586853226 0 0.23757744743232836
		1.0079654112529923 0 0.3359884704176625
		0.77038796382066199 0 0.23757744743232906
		0.67197694083532789 0 -9.7754656704855059e-16
		0.77038796382066133 0 -0.23757744743233128
		1.2455428586853226 0 0.23757744743232836
		1.3439538816706558 0 -1.9550931340971012e-15
		1.2455428586853217 0 -0.23757744743233197
		0.77038796382066199 0 0.23757744743232906
		;
createNode transform -n "Extra_Locator" -p "ControllerReference";
	rename -uid "15D3E98B-4DDD-63BD-70FF-2FBA3F8121ED";
createNode nurbsCurve -n "Extra_LocatorShape" -p "Extra_Locator";
	rename -uid "8D1277D9-4F1F-B58A-695F-5DABB1CD5DA5";
	setAttr -k off ".v";
	setAttr ".cc" -type "nurbsCurve" 
		1 7 0 no 3
		8 0 1 2 3 4 5 6 7
		8
		0 0 -1
		0 0 1
		0 0 0
		1 0 0
		-1 0 0
		0 0 0
		0 1 0
		0 -1 0
		;
createNode transform -n "Extra_Gear" -p "ControllerReference";
	rename -uid "32677399-4E86-C7C1-1194-E3BD5194C6AA";
createNode nurbsCurve -n "Extra_GearShape" -p "Extra_Gear";
	rename -uid "3341E2C7-4794-664D-3C66-00BA64C40C74";
	setAttr -k off ".v";
	setAttr ".cc" -type "nurbsCurve" 
		1 12 0 no 3
		13 0 1 2 3 4 5 6 7 8 9 10 11 12
		13
		0.11896706511256441 0.13481774260761892 0.44391452955550453
		-0.11896706511256441 0.13481774260761892 0.44391452955550453
		-0.32494746444294026 0.13481774260761892 0.32494746444294026
		-0.44391452955550453 0.13481774260761892 0.11896706511256441
		-0.44391452955550453 0.13481774260761892 -0.11896706511256441
		-0.32494746444294026 0.13481774260761892 -0.32494746444294026
		-0.11896706511256441 0.13481774260761892 -0.44391452955550453
		0.11896706511256441 0.13481774260761892 -0.44391452955550453
		0.32494746444294026 0.13481774260761892 -0.32494746444294026
		0.44391452955550453 0.13481774260761892 -0.11896706511256441
		0.44391452955550453 0.13481774260761892 0.11896706511256441
		0.32494746444294026 0.13481774260761892 0.32494746444294026
		0.11896706511256441 0.13481774260761892 0.44391452955550453
		;
createNode nurbsCurve -n "Extra_GearShape1" -p "Extra_Gear";
	rename -uid "6666F05E-4609-3F81-1A81-1F806D2B76F7";
	setAttr -k off ".v";
	setAttr ".cc" -type "nurbsCurve" 
		1 36 0 no 3
		37 0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27
		 28 29 30 31 32 33 34 35 36
		37
		-0.47609368359589999 0.13481774260761892 -0.5497506964344222
		-0.23804684179794999 0.13481774260761892 -0.68714610370322049
		-0.24137183319616951 0.13481774260761892 -0.83141691691409902
		-0.1642207616001955 0.13481774260761892 -0.97568773012497745
		0.1642207616001955 0.13481774260761892 -0.97568773012497745
		0.24137183319616951 0.13481774260761892 -0.83141691691409902
		0.23804684179794999 0.13481774260761892 -0.68714610370322049
		0.47609368359589999 0.13481774260761892 -0.5497506964344222
		0.59934378847566161 0.13481774260761892 -0.62476024814679765
		0.76283192485252116 0.13481774260761892 -0.63011404785579483
		0.92710904223912716 0.13481774260761892 -0.34563003805559334
		0.84071562167183156 0.13481774260761892 -0.20665666876730165
		0.71414052539384976 0.13481774260761892 -0.13745176305520818
		0.71414052539384976 0.13481774260761892 0.13745176305520818
		0.84071562167183156 0.13481774260761892 0.20665666876730165
		0.92710904223912716 0.13481774260761892 0.34563003805559334
		0.76283192485252116 0.13481774260761892 0.63011404785579483
		0.59934378847566161 0.13481774260761892 0.62476024814679765
		0.47609368359589999 0.13481774260761892 0.5497506964344222
		0.23804684179794999 0.13481774260761892 0.68714610370322049
		0.24137183319616951 0.13481774260761892 0.83141691691409902
		0.1642207616001955 0.13481774260761892 0.97568773012497745
		-0.1642207616001955 0.13481774260761892 0.97568773012497745
		-0.24137183319616951 0.13481774260761892 0.83141691691409902
		-0.23804684179794999 0.13481774260761892 0.68714610370322049
		-0.47609368359589999 0.13481774260761892 0.5497506964344222
		-0.59934378847566161 0.13481774260761892 0.62476024814679765
		-0.76283192485252116 0.13481774260761892 0.63011404785579483
		-0.92710904223912716 0.13481774260761892 0.34563003805559334
		-0.84071562167183156 0.13481774260761892 0.20665666876730165
		-0.71414052539384976 0.13481774260761892 0.13745176305520818
		-0.71414052539384976 0.13481774260761892 -0.13745176305520818
		-0.84071562167183156 0.13481774260761892 -0.20665666876730165
		-0.92710904223912716 0.13481774260761892 -0.34563003805559334
		-0.76283192485252116 0.13481774260761892 -0.63011404785579483
		-0.59934378847566161 0.13481774260761892 -0.62476024814679765
		-0.47609368359589999 0.13481774260761892 -0.5497506964344222
		;
createNode transform -n "Extra_Flag" -p "ControllerReference";
	rename -uid "9DBCD917-44DA-9E3A-59B9-85917B8C8BF8";
	setAttr ".s" -type "double3" 0.17301230358841713 0.17301230358841713 0.17301230358841713 ;
createNode nurbsCurve -n "Extra_FlagShape" -p "Extra_Flag";
	rename -uid "7C595AD9-44AB-DA9E-1CBB-CB8C3672BB92";
	setAttr -k off ".v";
	setAttr ".cc" -type "nurbsCurve" 
		1 3 0 no 3
		4 0 1 2 3
		4
		0 -4.4881686811493182e-08 0
		0 7.0737638438057449 0
		3 5.0737638438057449 0
		0 3.0737638438057449 0
		;
createNode transform -n "Extra_Fist" -p "ControllerReference";
	rename -uid "D16198CE-4BDE-6B65-AF49-D198A044A2D1";
createNode nurbsCurve -n "Extra_FistShape" -p "Extra_Fist";
	rename -uid "1290ACAA-4E6B-B1C3-FBC6-999F99DC28DA";
	setAttr -k off ".v";
	setAttr ".cc" -type "nurbsCurve" 
		1 71 0 no 3
		72 0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27
		 28 29 30 31 32 33 34 35 36 37 38 39 40 41 42 43 44 45 46 47 48 49 50 51 52 53 54
		 55 56 57 58 59 60 61 62 63 64 65 66 67 68 69 70 71
		72
		-0.71776027730316372 0.016310964484280897 0.71193100951433064
		-0.68937427763580728 0.016310964484280897 0.77757363374509281
		-0.41058320947426713 0.016057518058679394 0.80393206200763889
		-0.35913358507718335 0.016057518058679394 0.73524808066965996
		-0.31097876421291709 0.016057518058679394 0.81635093686210702
		0.068683981337979191 0.015550625207476588 0.79506143711159039
		0.0805959633412449 0.015550625207476588 0.72054818798477871
		0.14370412331599336 0.015550625207476588 0.78695115149234507
		0.42452276288234447 0.015043732356273877 0.73347395569044915
		0.45671045893372142 0.015043732356273877 0.6445142603043581
		0.52514099384609902 0.015043732356273877 0.69596388470144255
		0.81305613332928905 0.014790285930672909 0.55808902917428116
		0.80443895485884187 0.014790285930672909 0.4980222263067498
		0.73271361641364563 0.014536839505070977 0.15181440893523812
		0.47318447659781304 0.014790285930672909 -0.063868499251552691
		0.31224599634092376 0.015043732356273877 -0.017741249792097954
		0.32137006766257431 0.015043732356273877 0.027372213964951136
		0.4306054770967776 0.015043732356273877 0.26459806832786087
		0.45671045893372142 0.015043732356273877 0.6445142603043581
		0.4306054770967776 0.015043732356273877 0.26459806832786087
		0.32137006766257431 0.015043732356273877 0.027372213964951136
		0.24254822930053904 0.015043732356273877 -0.01926192834570634
		0.0063361606400349785 0.01529717878187508 0.050182392269077059
		0.0050689285120279828 0.01529717878187508 0.099857891686951361
		0.098083766707741549 0.01529717878187508 0.39664365606618995
		0.0805959633412449 0.015550625207476588 0.72054818798477871
		0.098083766707741549 0.01529717878187508 0.39664365606618995
		0.0050689285120279828 0.01529717878187508 0.099857891686951361
		-0.038777303117014071 0.01529717878187508 0.053984088653098082
		-0.27904451458714058 0.015550625207476588 0.088199356109286794
		-0.29551853225123176 0.015550625207476588 0.14775926612561588
		-0.29197028229281191 0.015804071633077885 0.42731067356395913
		-0.34848883520192325 0.016057518058679394 0.71066377738632358
		-0.29197028229281191 0.015804071633077885 0.42731067356395913
		-0.29551853225123176 0.015550625207476588 0.14775926612561588
		-0.34367335311549763 0.015804071633077885 0.076794266957223994
		-0.55200631495984698 0.015804071633077885 0.022049839027321699
		-0.62753334978906372 0.016057518058679394 0.045366910182650398
		-0.69013461691261047 0.016057518058679394 0.37814206699728786
		-0.71776027730316372 0.016310964484280897 0.71193100951433064
		-0.69013461691261047 0.016057518058679394 0.37814206699728786
		-0.6536383316260086 0.016057518058679394 0.18450899783781888
		-0.73296706283924717 0.016057518058679394 0.077808052659629631
		-0.82167331179973679 0.016057518058679394 -0.39841778104539954
		-0.51322901184283365 0.015550625207476588 -0.7806149908523099
		-0.36800420997323163 0.01529717878187508 -0.80215793702842841
		-0.51322901184283365 0.015550625207476588 -0.7806149908523099
		-0.82167331179973679 0.016057518058679394 -0.39841778104539954
		-0.73296706283924717 0.016057518058679394 0.077808052659629631
		-0.6536383316260086 0.016057518058679394 0.18450899783781888
		-0.31503390702253953 0.015804071633077885 0.34189922813628804
		-0.24508269355655307 0.015804071633077885 0.33860442460346946
		-0.15536265889365769 0.015550625207476588 0.13610073054795149
		-0.2344379436812945 0.015550625207476588 -0.11531812364863671
		-0.54085467223338579 0.015804071633077885 -0.23722585436290988
		-0.54288224363819737 0.015804071633077885 -0.36699042427082601
		-0.54085467223338579 0.015804071633077885 -0.23722585436290988
		-0.2344379436812945 0.015550625207476588 -0.11531812364863671
		-0.17538492651616844 0.015550625207476588 0.072739124147601586
		-0.038777303117014071 0.01529717878187508 0.053984088653098082
		0.0050689285120279828 0.01529717878187508 0.099857891686951361
		0.0063361606400349785 0.01529717878187508 0.050182392269077059
		0.24254822930053904 0.015043732356273877 -0.01926192834570634
		0.32137006766257431 0.015043732356273877 0.027372213964951136
		0.31224599634092376 0.015043732356273877 -0.017741249792097954
		0.47318447659781304 0.014790285930672909 -0.063868499251552691
		0.73271361641364563 0.014536839505070977 0.15181440893523812
		0.76768922314663846 0.014536839505070977 0.32137006766257431
		0.83029049027018398 0.014536839505070977 0.029399785369762298
		0.75020141978014243 0.014283393079469575 -0.59635943944009295
		0.53046336878372891 0.014536839505070977 -0.81102856192447725
		0.36597663856842066 0.014536839505070977 -0.81483025830849931
		;
createNode transform -n "Rotate_Rotate5" -p "ControllerReference";
	rename -uid "C3DC7650-4121-5071-048B-42993BFF3B1F";
createNode nurbsCurve -n "Rotate_Rotate5Shape" -p "Rotate_Rotate5";
	rename -uid "E077010D-46D7-BE5B-7F47-CA85F75C693F";
	setAttr -k off ".v";
	setAttr ".cc" -type "nurbsCurve" 
		3 17 0 no 3
		22 0 0 0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 17 17
		20
		-0.27500000000000002 0 0.44080000000000003
		-0.27500000000000002 0 0.44080000000000003
		-0.27500000000000002 0 0.44080000000000003
		0 0 0.81000000000000005
		0 0 0.81000000000000005
		0 0 0.81000000000000005
		0 0 0.81000000000000005
		-0.36170000000000002 0 1.0948
		-0.36170000000000002 0 1.0948
		-0.36170000000000002 0 1.0948
		-0.36170000000000002 0 1.0948
		0 0 0.81000000000000005
		0 0 0.81000000000000005
		0 0 0.81000000000000005
		0 0 0.81000000000000005
		-0.1053 0 0.81000000000000005
		-0.31840000000000002 0 0.76780000000000004
		-0.58760000000000001 0 0.5877
		-0.76780000000000004 0 0.318
		-0.83109999999999995 0 0
		;
createNode transform -n "Rotate_Rotate4" -p "ControllerReference";
	rename -uid "C3602A0E-43DB-D120-4CF5-279B9B67B289";
createNode nurbsCurve -n "Rotate_Rotate4Shape" -p "Rotate_Rotate4";
	rename -uid "449EB9D1-404E-3BE8-F3BB-B794F6D40271";
	setAttr -k off ".v";
	setAttr ".cc" -type "nurbsCurve" 
		3 29 0 no 3
		34 0 0 0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25
		 26 27 28 29 29 29
		32
		-0.35699999999999998 0 0.63880000000000003
		-0.35699999999999998 0 0.63880000000000003
		-0.35699999999999998 0 0.63880000000000003
		-0.43559999999999999 0 0.2833
		-0.43559999999999999 0 0.2833
		-0.43559999999999999 0 0.2833
		-0.43559999999999999 0 0.2833
		-0.1009 0 0.88819999999999999
		-0.1009 0 0.88819999999999999
		-0.1009 0 0.88819999999999999
		-0.1009 0 0.88819999999999999
		-0.79049999999999998 0 0.83940000000000003
		-0.79049999999999998 0 0.83940000000000003
		-0.79049999999999998 0 0.83940000000000003
		-0.79049999999999998 0 0.83940000000000003
		-0.45429999999999998 0 0.76649999999999996
		-0.45429999999999998 0 0.76649999999999996
		-0.45429999999999998 0 0.76649999999999996
		-0.45429999999999998 0 0.76649999999999996
		-0.64639999999999997 0 0.64639999999999997
		-0.84460000000000002 0 0.34989999999999999
		-0.91420000000000001 0 0
		-0.91420000000000001 0 0
		-0.91420000000000001 0 0
		-0.91420000000000001 0 0
		-0.74790000000000001 0 0
		-0.74790000000000001 0 0
		-0.74790000000000001 0 0
		-0.74790000000000001 0 0
		-0.69110000000000005 0 0.28620000000000001
		-0.52869999999999995 0 0.52890000000000004
		-0.35699999999999998 0 0.63880000000000003
		;
createNode transform -n "Rotate_Rotate3" -p "ControllerReference";
	rename -uid "3679A477-49EC-DCCE-C310-1BA8786EBBCA";
createNode nurbsCurve -n "Rotate_Rotate3Shape" -p "Rotate_Rotate3";
	rename -uid "EB1E0492-4212-5A7E-4180-2E899CE6B4BC";
	setAttr -k off ".v";
	setAttr ".cc" -type "nurbsCurve" 
		3 37 0 no 3
		42 0 0 0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25
		 26 27 28 29 30 31 32 33 34 35 36 37 37 37
		40
		-0.27500000000000002 0 0.44080000000000003
		-0.27500000000000002 0 0.44080000000000003
		-0.27500000000000002 0 0.44080000000000003
		0 0 0.81000000000000005
		0 0 0.81000000000000005
		0 0 0.81000000000000005
		0 0 0.81000000000000005
		-0.36170000000000002 0 1.0948
		-0.36170000000000002 0 1.0948
		-0.36170000000000002 0 1.0948
		-0.36170000000000002 0 1.0948
		0 0 0.81000000000000005
		0 0 0.81000000000000005
		0 0 0.81000000000000005
		0 0 0.81000000000000005
		-0.1053 0 0.81000000000000005
		-0.31840000000000002 0 0.76780000000000004
		-0.58760000000000001 0 0.5877
		-0.76780000000000004 0 0.318
		-0.83109999999999995 0 0
		-0.76780000000000004 0 -0.318
		-0.58760000000000001 0 -0.5877
		-0.31840000000000002 0 -0.76780000000000004
		-0.1053 0 -0.81000000000000005
		0.0086999999999999994 0 -0.81110000000000004
		0.0086999999999999994 0 -0.81110000000000004
		0.0086999999999999994 0 -0.81110000000000004
		0.0086999999999999994 0 -0.81110000000000004
		-0.27500000000000002 0 -0.44080000000000003
		-0.27500000000000002 0 -0.44080000000000003
		-0.27500000000000002 0 -0.44080000000000003
		-0.27500000000000002 0 -0.44080000000000003
		0.0086999999999999994 0 -0.81110000000000004
		0.0086999999999999994 0 -0.81110000000000004
		0.0086999999999999994 0 -0.81110000000000004
		0.0086999999999999994 0 -0.81110000000000004
		-0.36170000000000002 0 -1.0948
		-0.36170000000000002 0 -1.0948
		-0.36170000000000002 0 -1.0948
		-0.36170000000000002 0 -1.0948
		;
createNode transform -n "Rotate_Rotate2" -p "ControllerReference";
	rename -uid "39032CE0-4AC9-A2C1-9B7F-0BBC1B4F9B29";
createNode nurbsCurve -n "Rotate_Rotate2Shape" -p "Rotate_Rotate2";
	rename -uid "029C90FD-4921-6FAA-7E7C-5D8DB42C78FD";
	setAttr -k off ".v";
	setAttr ".cc" -type "nurbsCurve" 
		3 47 0 no 3
		52 0 0 0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25
		 26 27 28 29 30 31 32 33 34 35 36 37 38 39 40 41 42 43 44 45 46 47 47 47
		50
		-0.35699999999999998 0 0.63880000000000003
		-0.35699999999999998 0 0.63880000000000003
		-0.35699999999999998 0 0.63880000000000003
		-0.43559999999999999 0 0.2833
		-0.43559999999999999 0 0.2833
		-0.43559999999999999 0 0.2833
		-0.43559999999999999 0 0.2833
		-0.1009 0 0.88819999999999999
		-0.1009 0 0.88819999999999999
		-0.1009 0 0.88819999999999999
		-0.1009 0 0.88819999999999999
		-0.79049999999999998 0 0.83940000000000003
		-0.79049999999999998 0 0.83940000000000003
		-0.79049999999999998 0 0.83940000000000003
		-0.79049999999999998 0 0.83940000000000003
		-0.45429999999999998 0 0.76649999999999996
		-0.45429999999999998 0 0.76649999999999996
		-0.45429999999999998 0 0.76649999999999996
		-0.45429999999999998 0 0.76649999999999996
		-0.64639999999999997 0 0.64639999999999997
		-0.84460000000000002 0 0.34989999999999999
		-0.91420000000000001 0 0
		-0.84460000000000002 0 -0.34989999999999999
		-0.64639999999999997 0 -0.64639999999999997
		-0.45279999999999998 0 -0.76480000000000004
		-0.45279999999999998 0 -0.76480000000000004
		-0.45279999999999998 0 -0.76480000000000004
		-0.45279999999999998 0 -0.76480000000000004
		-0.79049999999999998 0 -0.83940000000000003
		-0.79049999999999998 0 -0.83940000000000003
		-0.79049999999999998 0 -0.83940000000000003
		-0.79049999999999998 0 -0.83940000000000003
		-0.1009 0 -0.88819999999999999
		-0.1009 0 -0.88819999999999999
		-0.1009 0 -0.88819999999999999
		-0.1009 0 -0.88819999999999999
		-0.43559999999999999 0 -0.2833
		-0.43559999999999999 0 -0.2833
		-0.43559999999999999 0 -0.2833
		-0.43559999999999999 0 -0.2833
		-0.35580000000000001 0 -0.63629999999999998
		-0.35580000000000001 0 -0.63629999999999998
		-0.35580000000000001 0 -0.63629999999999998
		-0.35580000000000001 0 -0.63629999999999998
		-0.52869999999999995 0 -0.52890000000000004
		-0.69110000000000005 0 -0.28620000000000001
		-0.74790000000000001 0 0
		-0.69110000000000005 0 0.28620000000000001
		-0.52869999999999995 0 0.52890000000000004
		-0.35699999999999998 0 0.63880000000000003
		;
createNode transform -n "Rotate_Rotate1" -p "ControllerReference";
	rename -uid "659D7E23-4393-7A98-76CA-869DE7E21F8C";
createNode nurbsCurve -n "Rotate_Rotate1Shape" -p "Rotate_Rotate1";
	rename -uid "93CE4F99-47D6-552B-DEFE-5A9F14311DBA";
	setAttr -k off ".v";
	setAttr ".cc" -type "nurbsCurve" 
		3 53 0 no 3
		58 0 0 0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25
		 26 27 28 29 30 31 32 33 34 35 36 37 38 39 40 41 42 43 44 45 46 47 48 49 50 51 52
		 53 53 53
		56
		0.096000000000000266 0.60399999999999998 -0.098799999999999999
		0.50080000000000024 0.50049999999999972 -0.098799999999999999
		0.75120000000000009 0.32789999999999969 -0.098799999999999999
		0.75120000000000009 0.32789999999999969 -0.098799999999999999
		0.75120000000000009 0.32789999999999969 -0.33660000000000001
		0.75120000000000009 0.32789999999999969 -0.33660000000000001
		1.0016 -4.4479975258582274e-16 0
		1.0016 -4.4479975258582274e-16 0
		0.75120000000000009 0.32789999999999969 0.33660000000000001
		0.75120000000000009 0.32789999999999969 0.33660000000000001
		0.75120000000000009 0.32789999999999969 0.098799999999999999
		0.75120000000000009 0.32789999999999969 0.098799999999999999
		0.50080000000000024 0.50049999999999972 0.098799999999999999
		0.096000000000000266 0.60399999999999998 0.098799999999999999
		0.096000000000000266 0.60399999999999998 0.098799999999999999
		0.096000000000000224 0.50049999999999994 0.50080000000000002
		0.096000000000000141 0.32789999999999997 0.75119999999999998
		0.096000000000000141 0.32789999999999997 0.75119999999999998
		0.33660000000000018 0.32789999999999986 0.75119999999999998
		0.33660000000000018 0.32789999999999986 0.75119999999999998
		0 0 1.0016
		0 0 1.0016
		-0.33659999999999984 0.32790000000000019 0.75119999999999998
		-0.33659999999999984 0.32790000000000019 0.75119999999999998
		-0.095999999999999863 0.32790000000000008 0.75119999999999998
		-0.095999999999999863 0.32790000000000008 0.75119999999999998
		-0.09599999999999978 0.50049999999999994 0.50080000000000002
		-0.095999999999999738 0.60399999999999998 0.098799999999999999
		-0.095999999999999738 0.60399999999999998 0.098799999999999999
		-0.5007999999999998 0.50050000000000017 0.098799999999999999
		-0.75119999999999987 0.32790000000000036 0.098799999999999999
		-0.75119999999999987 0.32790000000000036 0.098799999999999999
		-0.75119999999999987 0.32790000000000036 0.33660000000000001
		-0.75119999999999987 0.32790000000000036 0.33660000000000001
		-1.0016 4.4479975258582274e-16 0
		-1.0016 4.4479975258582274e-16 0
		-0.75119999999999987 0.32790000000000036 -0.33660000000000001
		-0.75119999999999987 0.32790000000000036 -0.33660000000000001
		-0.75119999999999987 0.32790000000000036 -0.098799999999999999
		-0.75119999999999987 0.32790000000000036 -0.098799999999999999
		-0.5007999999999998 0.50050000000000017 -0.098799999999999999
		-0.095999999999999738 0.60399999999999998 -0.098799999999999999
		-0.095999999999999738 0.60399999999999998 -0.098799999999999999
		-0.09599999999999978 0.50049999999999994 -0.50080000000000002
		-0.095999999999999863 0.32790000000000008 -0.75119999999999998
		-0.095999999999999863 0.32790000000000008 -0.75119999999999998
		-0.33659999999999984 0.32790000000000019 -0.75119999999999998
		-0.33659999999999984 0.32790000000000019 -0.75119999999999998
		0 0 -1.0016
		0 0 -1.0016
		0.33660000000000018 0.32789999999999986 -0.75119999999999998
		0.33660000000000018 0.32789999999999986 -0.75119999999999998
		0.096000000000000141 0.32789999999999997 -0.75119999999999998
		0.096000000000000141 0.32789999999999997 -0.75119999999999998
		0.096000000000000224 0.50049999999999994 -0.50080000000000002
		0.096000000000000266 0.60399999999999998 -0.098799999999999999
		;
createNode transform -n "Arrow_Arrow_thin2" -p "ControllerReference";
	rename -uid "09EF4585-4BB0-B574-59A9-E7AA6A2758BB";
createNode nurbsCurve -n "Arrow_Arrow_thin2Shape" -p "Arrow_Arrow_thin2";
	rename -uid "2D710125-4E14-25DB-8EBE-57B020225E28";
	setAttr -k off ".v";
	setAttr ".cc" -type "nurbsCurve" 
		1 7 0 no 3
		8 0 1 2 3 4 5 6 7
		8
		0.48720000000000002 0 -0.48720000000000002
		0.97440000000000004 0 0
		0.48720000000000002 0 0.48720000000000002
		0.97440000000000004 0 0
		-0.97440000000000004 0 0
		-0.48720000000000002 0 0.48720000000000002
		-0.97440000000000004 0 0
		-0.48720000000000002 0 -0.48720000000000002
		;
createNode transform -n "Arrow_Arrow_thin1" -p "ControllerReference";
	rename -uid "CC1D14D7-45E0-5BDA-459B-3A8C53E105BD";
createNode nurbsCurve -n "Arrow_Arrow_thin1Shape" -p "Arrow_Arrow_thin1";
	rename -uid "02407AED-42FA-2A6B-0F5D-B3B23D7E67DA";
	setAttr -k off ".v";
	setAttr ".cc" -type "nurbsCurve" 
		1 2 0 no 3
		3 0 1 2
		3
		0 0 -1
		1 0 0
		0 0 1
		;
createNode nurbsCurve -n "Arrow_Arrow_thin1Shape1" -p "Arrow_Arrow_thin1";
	rename -uid "968911AD-4B4B-84A9-40A7-C0BDFFB49621";
	setAttr -k off ".v";
	setAttr ".cc" -type "nurbsCurve" 
		1 1 0 no 3
		2 0 1
		2
		-1 0 0
		1 0 0
		;
createNode transform -n "Arrow_Arrow_bold2" -p "ControllerReference";
	rename -uid "1B238666-4F67-5AE8-5B7C-199566D8B0CE";
createNode nurbsCurve -n "Arrow_Arrow_bold2Shape" -p "Arrow_Arrow_bold2";
	rename -uid "7E761B6B-4074-944A-BF9B-068F7EF7E11A";
	setAttr -k off ".v";
	setAttr ".cc" -type "nurbsCurve" 
		1 10 0 no 3
		11 0 1 2 3 4 5 6 7 8 9 10
		11
		-0.95440000000000003 0 0
		-0.2545 0 0.46660000000000001
		-0.2545 0 0.23330000000000001
		0.2545 0 0.23330000000000001
		0.2545 0 0.46660000000000001
		0.95440000000000003 0 0
		0.2545 0 -0.46660000000000001
		0.2545 0 -0.23330000000000001
		-0.2545 0 -0.23330000000000001
		-0.2545 0 -0.46660000000000001
		-0.95440000000000003 0 0
		;
createNode transform -n "Arrow_Arrow_bold1" -p "ControllerReference";
	rename -uid "D94701B1-4562-6223-5585-48859F5E3ABF";
	setAttr ".r" -type "double3" 0 -89.999999999999986 0 ;
createNode nurbsCurve -n "Arrow_Arrow_bold1Shape" -p "Arrow_Arrow_bold1";
	rename -uid "CDBD8F89-47D3-32A5-CE5B-B7B7B2F821EE";
	setAttr -k off ".v";
	setAttr ".cc" -type "nurbsCurve" 
		1 7 0 no 3
		8 0 1 2 3 4 5 6 7
		8
		-2.4651903288156619e-32 0 -0.99999999999999978
		1 0 0
		0.5 0 0
		0.5 0 1
		-0.5 0 1
		-0.5 0 0
		-1 0 0
		-2.4651903288156619e-32 0 -0.99999999999999978
		;
createNode transform -n "Base_Base6" -p "ControllerReference";
	rename -uid "F9097189-46CF-DDF1-F700-CEBF2F4ACCF7";
createNode nurbsCurve -n "Base_Base6Shape" -p "Base_Base6";
	rename -uid "BE375BB1-4DC8-2055-BD6E-B8AED2A005BA";
	setAttr -k off ".v";
	setAttr ".cc" -type "nurbsCurve" 
		1 56 0 no 3
		57 0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27
		 28 29 30 31 32 33 34 35 36 37 38 39 40 41 42 43 44 45 46 47 48 49 50 51 52 53 54
		 55 56
		57
		0 0.81000000000000005 0
		0 0.74829999999999997 0.31
		0 0.57279999999999998 0.57279999999999998
		0 0.31 0.74829999999999997
		0 0 0.81000000000000005
		0 -0.31 0.74829999999999997
		0 -0.57279999999999998 0.57279999999999998
		0 -0.74829999999999997 0.31
		0 -0.81000000000000005 0
		0 -0.74829999999999997 -0.31
		0 -0.57279999999999998 -0.57279999999999998
		0 -0.31 -0.74829999999999997
		0 0 -0.81000000000000005
		0 0.31 -0.74829999999999997
		0 0.57279999999999998 -0.57279999999999998
		0 0.74829999999999997 -0.31
		0 0.81000000000000005 0
		0.31 0.74829999999999997 0
		0.57279999999999998 0.57279999999999998 0
		0.74829999999999997 0.31 0
		0.81000000000000005 0 0
		0.74829999999999997 -0.31 0
		0.57279999999999998 -0.57279999999999998 0
		0.31 -0.74829999999999997 0
		0 -0.81000000000000005 0
		-0.31 -0.74829999999999997 0
		-0.57279999999999998 -0.57279999999999998 0
		-0.74829999999999997 -0.31 0
		-0.81000000000000005 0 0
		-0.74829999999999997 0 0.31
		-0.57279999999999998 0 0.57279999999999998
		-0.31 0 0.74829999999999997
		0 0 0.81000000000000005
		0.31 0 0.74829999999999997
		0.57279999999999998 0 0.57279999999999998
		0.74829999999999997 0 0.31
		0.81000000000000005 0 0
		0.74829999999999997 0 -0.31
		0.57279999999999998 0 -0.57279999999999998
		0.31 0 -0.74829999999999997
		0 0 -0.81000000000000005
		-0.31 0 -0.74829999999999997
		-0.57279999999999998 0 -0.57279999999999998
		-0.74829999999999997 0 -0.31
		-0.81000000000000005 0 0
		-0.74829999999999997 0.31 0
		-0.57279999999999998 0.57279999999999998 0
		-0.31 0.74829999999999997 0
		0 0.81000000000000005 0
		0 1.2582 0
		0 -1.2582 0
		0 0 0
		-1.2582 0 0
		1.2582 0 0
		0 0 0
		0 0 -1.2582
		0 0 1.2582
		;
createNode transform -n "Base_Base5" -p "ControllerReference";
	rename -uid "B433ED07-432A-C0EF-AB99-B5A7CB2152A4";
createNode nurbsCurve -n "Base_Base5Shape" -p "Base_Base5";
	rename -uid "7D6AC4B1-48DC-E2A6-184E-57AC16785D55";
	setAttr -k off ".v";
	setAttr ".cc" -type "nurbsCurve" 
		1 31 0 no 3
		32 0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27
		 28 29 30 31
		32
		0.81790000000000007 2.7755575615628914e-17 0
		0.79419999999999991 2.7755575615628914e-17 -0.19570000000000001
		0.72419999999999995 1.6653345369377348e-16 -0.38009999999999999
		0.61219999999999997 8.3266726846886741e-17 -0.54239999999999999
		0.4645999999999999 0 -0.67310000000000003
		0.28999999999999992 -1.3877787807814457e-17 -0.76480000000000004
		0.098599999999999993 -3.4694469519536142e-18 -0.81200000000000006
		-0.098599999999999993 3.4694469519536142e-18 -0.81200000000000006
		-0.28999999999999992 1.3877787807814457e-17 -0.76480000000000004
		-0.4645999999999999 0 -0.67310000000000003
		-0.61219999999999997 -8.3266726846886741e-17 -0.54239999999999999
		-0.72419999999999995 -1.6653345369377348e-16 -0.38009999999999999
		-0.79419999999999991 -2.7755575615628914e-17 -0.19570000000000001
		-0.81790000000000007 -2.7755575615628914e-17 0
		-0.79419999999999991 -2.7755575615628914e-17 0.19570000000000001
		-0.72419999999999995 -1.6653345369377348e-16 0.38009999999999999
		-0.61219999999999997 -8.3266726846886741e-17 0.54239999999999999
		-0.4645999999999999 0 0.67310000000000003
		-0.28999999999999992 1.3877787807814457e-17 0.76480000000000004
		-0.098599999999999993 3.4694469519536142e-18 0.81200000000000006
		0.098599999999999993 -3.4694469519536142e-18 0.81200000000000006
		0.28999999999999992 -1.3877787807814457e-17 0.76480000000000004
		0.4645999999999999 0 0.67310000000000003
		0.61219999999999997 8.3266726846886741e-17 0.54239999999999999
		0.72419999999999995 1.6653345369377348e-16 0.38009999999999999
		0.79419999999999991 2.7755575615628914e-17 0.19570000000000001
		0.81790000000000007 2.7755575615628914e-17 0
		1.1536999999999995 1.6653345369377348e-16 0
		-1.1536999999999995 -1.6653345369377348e-16 0
		0 0 0
		0 0 -1.1536999999999999
		0 0 1.1536999999999999
		;
createNode transform -n "Base_Base4" -p "ControllerReference";
	rename -uid "65C46C42-4D3E-B8E9-FD88-B2BC503B4E97";
createNode nurbsCurve -n "Base_Base4Shape" -p "Base_Base4";
	rename -uid "EA267D59-4967-ED75-1653-BBB6D0B547CE";
	setAttr -k off ".v";
	setAttr ".cc" -type "nurbsCurve" 
		1 19 0 no 3
		20 0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19
		20
		1.5 0 -0.5
		2 0 0
		1.5 0 0.5
		2 0 0
		-2 0 0
		-1.5 0 -0.5
		-2 0 0
		-1.5 0 0.5
		-2 0 0
		0 0 0
		0 0 2
		-0.5 0 1.5
		0 0 2
		0.5 0 1.5
		0 0 2
		0 0 -2
		0.5 0 -1.5
		0 0 -2
		-0.5 0 -1.5
		0 0 -2
		;
createNode transform -n "Base_Base3" -p "ControllerReference";
	rename -uid "EE0BF64D-49A1-FB78-5C33-94BDC099A4F5";
createNode nurbsCurve -n "Base_Base3Shape" -p "Base_Base3";
	rename -uid "05F67F85-499B-33AD-AE0F-F29353CFB16E";
	setAttr -k off ".v";
	setAttr ".cc" -type "nurbsCurve" 
		1 1 0 no 3
		2 0 1
		2
		-0.69530000000000003 0 -0.38400000000000001
		-1.1519999999999999 0 -0.38400000000000001
		;
createNode nurbsCurve -n "Base_Base3Shape1" -p "Base_Base3";
	rename -uid "F5FC9683-46F6-70B6-DE20-45805074C14D";
	setAttr -k off ".v";
	setAttr ".cc" -type "nurbsCurve" 
		3 2 0 no 3
		7 0 0 0 1 2 2 2
		5
		-0.38400000000000001 0 -0.69530000000000003
		-0.44929999999999998 0 -0.65949999999999998
		-0.56999999999999995 0 -0.56999999999999995
		-0.65949999999999998 0 -0.44929999999999998
		-0.69530000000000003 0 -0.38400000000000001
		;
createNode nurbsCurve -n "Base_Base3Shape2" -p "Base_Base3";
	rename -uid "9D026962-4037-4B0F-D441-879DF2CA1F1E";
	setAttr -k off ".v";
	setAttr ".cc" -type "nurbsCurve" 
		1 5 0 no 3
		6 0 1 2 3 4 5
		6
		-1.1519999999999999 0 -0.38400000000000001
		-1.1519999999999999 0 -0.76800000000000002
		-1.9199999999999999 0 0
		-1.1519999999999999 0 0.76800000000000002
		-1.1519999999999999 0 0.38400000000000001
		-0.69530000000000003 0 0.38400000000000001
		;
createNode nurbsCurve -n "Base_Base3Shape3" -p "Base_Base3";
	rename -uid "6A82FB6E-479D-F7DD-DC20-36B91F33020A";
	setAttr -k off ".v";
	setAttr ".cc" -type "nurbsCurve" 
		3 2 0 no 3
		7 0 0 0 1 2 2 2
		5
		-0.69530000000000003 0 0.38400000000000001
		-0.65949999999999998 0 0.44929999999999998
		-0.56999999999999995 0 0.56999999999999995
		-0.44929999999999998 0 0.65949999999999998
		-0.38400000000000001 0 0.69530000000000003
		;
createNode nurbsCurve -n "Base_Base3Shape4" -p "Base_Base3";
	rename -uid "755D976A-4A50-EFCF-43C6-1CB9F27CDE2A";
	setAttr -k off ".v";
	setAttr ".cc" -type "nurbsCurve" 
		3 2 0 no 3
		7 0 0 0 1 2 2 2
		5
		0.38400000000000001 0 0.69530000000000003
		0.44929999999999998 0 0.65949999999999998
		0.56999999999999995 0 0.56999999999999995
		0.65949999999999998 0 0.44929999999999998
		0.69530000000000003 0 0.38400000000000001
		;
createNode nurbsCurve -n "Base_Base3Shape5" -p "Base_Base3";
	rename -uid "603E0E4E-460D-8F1A-9892-C0869F6A7342";
	setAttr -k off ".v";
	setAttr ".cc" -type "nurbsCurve" 
		3 2 0 no 3
		7 0 0 0 1 2 2 2
		5
		0.69530000000000003 0 -0.38400000000000001
		0.65949999999999998 0 -0.44929999999999998
		0.56999999999999995 0 -0.56999999999999995
		0.44929999999999998 0 -0.65949999999999998
		0.38400000000000001 0 -0.69530000000000003
		;
createNode nurbsCurve -n "Base_Base3Shape6" -p "Base_Base3";
	rename -uid "7A9BA6F3-45B3-FAE6-E45D-978F78FEBC95";
	setAttr -k off ".v";
	setAttr ".cc" -type "nurbsCurve" 
		1 6 0 no 3
		7 0 1 2 3 4 5 6
		7
		-0.38400000000000001 0 0.69530000000000003
		-0.38400000000000001 0 1.1519999999999999
		-0.76800000000000002 0 1.1519999999999999
		0 0 1.9199999999999999
		0.76800000000000002 0 1.1519999999999999
		0.38400000000000001 0 1.1519999999999999
		0.38400000000000001 0 0.69530000000000003
		;
createNode nurbsCurve -n "Base_Base3Shape7" -p "Base_Base3";
	rename -uid "0ED6BECB-4D1B-3B84-A2AB-DAB1F62F5C3A";
	setAttr -k off ".v";
	setAttr ".cc" -type "nurbsCurve" 
		1 6 0 no 3
		7 0 1 2 3 4 5 6
		7
		0.69530000000000003 0 0.38400000000000001
		1.1519999999999999 0 0.38400000000000001
		1.1519999999999999 0 0.76800000000000002
		1.9199999999999999 0 0
		1.1519999999999999 0 -0.76800000000000002
		1.1519999999999999 0 -0.38400000000000001
		0.69530000000000003 0 -0.38400000000000001
		;
createNode nurbsCurve -n "Base_Base3Shape8" -p "Base_Base3";
	rename -uid "95FCA7AA-4BD6-07F3-F337-BFB12B47E85E";
	setAttr -k off ".v";
	setAttr ".cc" -type "nurbsCurve" 
		1 6 0 no 3
		7 0 1 2 3 4 5 6
		7
		0.38400000000000001 0 -0.69530000000000003
		0.38400000000000001 0 -1.1519999999999999
		0.76800000000000002 0 -1.1519999999999999
		0 0 -1.9199999999999999
		-0.76800000000000002 0 -1.1519999999999999
		-0.38400000000000001 0 -1.1519999999999999
		-0.38400000000000001 0 -0.69530000000000003
		;
createNode nurbsCurve -n "Base_Base3Shape9" -p "Base_Base3";
	rename -uid "243B893C-4EE2-9040-4B2E-46A3B41F794C";
	setAttr -k off ".v";
	setAttr ".cc" -type "nurbsCurve" 
		1 1 0 no 3
		2 0 1
		2
		-0.69530000000000003 0 -0.38400000000000001
		-1.1519999999999999 0 -0.38400000000000001
		;
createNode transform -n "Base_Base2" -p "ControllerReference";
	rename -uid "23592B61-4DD4-F1F8-1B6C-7EA799A19C6D";
createNode nurbsCurve -n "Base_Base2Shape" -p "Base_Base2";
	rename -uid "4B2D0487-47F5-414F-F0EC-2C91D638BB79";
	setAttr -k off ".v";
	setAttr ".cc" -type "nurbsCurve" 
		1 24 0 no 3
		25 0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24
		25
		0 0 -2
		0.59399999999999997 0 -1.0934999999999999
		0.29699999999999999 0 -1.0934999999999999
		0.29699999999999999 0 -0.29699999999999999
		1.0934999999999999 0 -0.29699999999999999
		1.0934999999999999 0 -0.59399999999999997
		2 0 0
		1.0934999999999999 0 0.59399999999999997
		1.0934999999999999 0 0.29699999999999999
		0.29699999999999999 0 0.29699999999999999
		0.29699999999999999 0 1.0934999999999999
		0.59399999999999997 0 1.0934999999999999
		0 0 2
		-0.59399999999999997 0 1.0934999999999999
		-0.29699999999999999 0 1.0934999999999999
		-0.29699999999999999 0 0.29699999999999999
		-1.0934999999999999 0 0.29699999999999999
		-1.0934999999999999 0 0.59399999999999997
		-2 0 0
		-1.0934999999999999 0 -0.59399999999999997
		-1.0934999999999999 0 -0.29699999999999999
		-0.29699999999999999 0 -0.29699999999999999
		-0.29699999999999999 0 -1.0934999999999999
		-0.59399999999999997 0 -1.0934999999999999
		0 0 -2
		;
createNode transform -n "Base_Base1" -p "ControllerReference";
	rename -uid "BC3C5228-4F1F-545F-D3D6-A297DA2E44ED";
createNode nurbsCurve -n "Base_Base1Shape" -p "Base_Base1";
	rename -uid "71CBC7A8-49C3-E5DA-CF4C-778C07E6965C";
	setAttr -k off ".v";
	setAttr ".cc" -type "nurbsCurve" 
		1 12 0 no 3
		13 0 1 2 3 4 5 6 7 8 9 10 11 12
		13
		-0.5 0 0.5
		-2 0 0.5
		-2 0 -0.5
		-0.5 0 -0.5
		-0.5 0 -2
		0.5 0 -2
		0.5 0 -0.5
		2 0 -0.5
		2 0 0.5
		0.5 0 0.5
		0.5 0 2
		-0.5 0 2
		-0.5 0 0.5
		;
createNode transform -n "ThreeD_PyramidHalf" -p "ControllerReference";
	rename -uid "B01124A2-4B6F-546F-1CEA-DFB31EDCD4F5";
createNode nurbsCurve -n "ThreeD_PyramidHalfShape" -p "ThreeD_PyramidHalf";
	rename -uid "16F9B665-432E-58B3-0434-E1876904B95D";
	setAttr -k off ".v";
	setAttr ".cc" -type "nurbsCurve" 
		1 8 0 no 3
		9 0 1 2 3 4 5 6 7 8
		9
		-1 0 0
		0 0 1
		0 1 0
		-1 0 0
		1 0 0
		0 1 0
		1 0 0
		0 0 1
		0 1 0
		;
createNode transform -n "ThreeD_Sim" -p "ControllerReference";
	rename -uid "0728ED01-49A8-BB06-FF41-368A8068D025";
createNode nurbsCurve -n "ThreeD_SimShape" -p "ThreeD_Sim";
	rename -uid "19E147E1-447B-E054-5D72-1EAFB2B8C978";
	setAttr -k off ".v";
	setAttr ".cc" -type "nurbsCurve" 
		1 13 0 no 3
		14 0 1 2 3 4 5 6 7 8 9 10 11 12 13
		14
		0 1 0
		1 0 0
		0 0 1
		-1 0 0
		0 0 -1
		0 1 0
		0 0 1
		0 -1 0
		0 0 -1
		1 0 0
		0 1 0
		-1 0 0
		0 -1 0
		1 0 0
		;
createNode transform -n "ThreeD_Sphere" -p "ControllerReference";
	rename -uid "536E95EA-43DB-EBE6-D233-B286B6549A24";
createNode nurbsCurve -n "ThreeD_SphereShape" -p "ThreeD_Sphere";
	rename -uid "A15A85FC-4A00-597F-3AE2-97ACD7B0CEAB";
	setAttr -k off ".v";
	setAttr ".cc" -type "nurbsCurve" 
		1 32 0 no 3
		33 0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27
		 28 29 30 31 32
		33
		0 0 1
		0 0.5 0.86599999999999999
		0 0.86599999999999999 0.5
		0 1 0
		0 0.86599999999999999 -0.5
		0 0.5 -0.86599999999999999
		0 0 -1
		0 -0.5 -0.86599999999999999
		0 -0.86599999999999999 -0.5
		0 -1 0
		0 -0.86599999999999999 0.5
		0 -0.5 0.86599999999999999
		0 0 1
		0.70709999999999995 0 0.70709999999999995
		1 0 0
		0.70709999999999995 0 -0.70709999999999995
		0 0 -1
		-0.70709999999999995 0 -0.70709999999999995
		-1 0 0
		-0.86599999999999999 0.5 0
		-0.5 0.86599999999999999 0
		0 1 0
		0.5 0.86599999999999999 0
		0.86599999999999999 0.5 0
		1 0 0
		0.86599999999999999 -0.5 0
		0.5 -0.86599999999999999 0
		0 -1 0
		-0.5 -0.86599999999999999 0
		-0.86599999999999999 -0.5 0
		-1 0 0
		-0.70709999999999995 0 0.70709999999999995
		0 0 1
		;
createNode transform -n "ThreeD_Cube" -p "ControllerReference";
	rename -uid "E4EE33AB-4BFF-4807-FF01-7EA956B5A06D";
createNode nurbsCurve -n "ThreeD_CubeShape" -p "ThreeD_Cube";
	rename -uid "7E4EFF55-4103-24CE-49A3-B698F1707CE6";
	setAttr -k off ".v";
	setAttr ".cc" -type "nurbsCurve" 
		1 15 0 no 3
		16 0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15
		16
		0.5 0.5 0.5
		0.5 0.5 -0.5
		-0.5 0.5 -0.5
		-0.5 -0.5 -0.5
		0.5 -0.5 -0.5
		0.5 0.5 -0.5
		-0.5 0.5 -0.5
		-0.5 0.5 0.5
		0.5 0.5 0.5
		0.5 -0.5 0.5
		0.5 -0.5 -0.5
		-0.5 -0.5 -0.5
		-0.5 -0.5 0.5
		0.5 -0.5 0.5
		-0.5 -0.5 0.5
		-0.5 0.5 0.5
		;
createNode transform -n "ThreeD_Pyramid" -p "ControllerReference";
	rename -uid "1BE44FBA-4409-B1BD-190D-2287FA5D71E1";
createNode nurbsCurve -n "ThreeD_PyramidShape" -p "ThreeD_Pyramid";
	rename -uid "620F2486-4924-EA8C-DB95-9BA5DDE0ECCA";
	setAttr -k off ".v";
	setAttr ".cc" -type "nurbsCurve" 
		1 1 0 no 3
		2 0 1
		2
		-1 0 -1
		0 1 0
		;
createNode nurbsCurve -n "ThreeD_PyramidShape1" -p "ThreeD_Pyramid";
	rename -uid "DEB24064-414C-37DB-067A-5985E111640C";
	setAttr -k off ".v";
	setAttr ".cc" -type "nurbsCurve" 
		1 4 0 no 3
		5 0 1 2 3 4
		5
		1 0 -1
		-1 0 -1
		-1 0 1
		1 0 1
		1 0 -1
		;
createNode nurbsCurve -n "ThreeD_PyramidShape2" -p "ThreeD_Pyramid";
	rename -uid "48330B99-4B2E-1480-4D61-518E7F310044";
	setAttr -k off ".v";
	setAttr ".cc" -type "nurbsCurve" 
		1 1 0 no 3
		2 0 1
		2
		0 1 0
		-1 0 1
		;
createNode nurbsCurve -n "ThreeD_PyramidShape3" -p "ThreeD_Pyramid";
	rename -uid "1C456BC8-409F-491E-37E3-5D81FB420092";
	setAttr -k off ".v";
	setAttr ".cc" -type "nurbsCurve" 
		1 1 0 no 3
		2 0 1
		2
		0 1 0
		1 0 1
		;
createNode nurbsCurve -n "ThreeD_PyramidShape4" -p "ThreeD_Pyramid";
	rename -uid "3CB1F03D-4613-0639-96CF-BEB3B6E472B0";
	setAttr -k off ".v";
	setAttr ".cc" -type "nurbsCurve" 
		1 1 0 no 3
		2 0 1
		2
		0 1 0
		1 0 -1
		;
createNode transform -n "ThreeD_Hexagon" -p "ControllerReference";
	rename -uid "1E46D43B-49B6-5B9A-0A84-9E99DD823320";
createNode nurbsCurve -n "ThreeD_HexagonShape" -p "ThreeD_Hexagon";
	rename -uid "54B02FD8-4C47-598E-0C12-949DC122E338";
	setAttr -k off ".v";
	setAttr ".cc" -type "nurbsCurve" 
		1 23 0 no 3
		24 0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23
		24
		-0.5 1 0.86599999999999999
		0.5 1 0.86599999999999999
		0.5 -1 0.86599999999999999
		1 -1 0
		1 1 0
		0.5 1 -0.86599999999999999
		0.5 -1 -0.86599999999999999
		-0.5 -1 -0.86599999999999999
		-0.5 1 -0.86599999999999999
		-1 1 0
		-1 -1 0
		-0.5 -1 0.86599999999999999
		-0.5 1 0.86599999999999999
		-1 1 0
		-0.5 1 -0.86599999999999999
		0.5 1 -0.86599999999999999
		1 1 0
		0.5 1 0.86599999999999999
		0.5 -1 0.86599999999999999
		-0.5 -1 0.86599999999999999
		-1 -1 0
		-0.5 -1 -0.86599999999999999
		0.5 -1 -0.86599999999999999
		1 -1 0
		;
createNode lightLinker -s -n "lightLinker1";
	rename -uid "F9C3F5AD-4B1A-09EF-A52D-5B9193B08960";
	setAttr -s 2 ".lnk";
	setAttr -s 2 ".slnk";
createNode shapeEditorManager -n "shapeEditorManager";
	rename -uid "4CBF06D2-47DE-F4B6-D170-E2BD91B71691";
createNode poseInterpolatorManager -n "poseInterpolatorManager";
	rename -uid "CEFB7E2C-4679-3E65-18E6-749A8D089C00";
createNode displayLayerManager -n "layerManager";
	rename -uid "23F2D83E-4D45-7B89-823E-20876F730825";
createNode displayLayer -n "defaultLayer";
	rename -uid "56FEBFA7-4E7A-CF0D-B64A-8EA2E9882976";
createNode renderLayerManager -n "renderLayerManager";
	rename -uid "91FA1686-4815-12BE-2CC8-E39A446B06CD";
createNode renderLayer -n "defaultRenderLayer";
	rename -uid "ABAB7C76-4FBE-504F-951A-45B66F1B1257";
	setAttr ".g" yes;
createNode script -n "uiConfigurationScriptNode";
	rename -uid "D12BDBFD-4C6D-E2F9-89BA-509811CC192B";
	setAttr ".b" -type "string" (
		"// Maya Mel UI Configuration File.\n//\n//  This script is machine generated.  Edit at your own risk.\n//\n//\n\nglobal string $gMainPane;\nif (`paneLayout -exists $gMainPane`) {\n\n\tglobal int $gUseScenePanelConfig;\n\tint    $useSceneConfig = $gUseScenePanelConfig;\n\tint    $nodeEditorPanelVisible = stringArrayContains(\"nodeEditorPanel1\", `getPanel -vis`);\n\tint    $nodeEditorWorkspaceControlOpen = (`workspaceControl -exists nodeEditorPanel1Window` && `workspaceControl -q -visible nodeEditorPanel1Window`);\n\tint    $menusOkayInPanels = `optionVar -q allowMenusInPanels`;\n\tint    $nVisPanes = `paneLayout -q -nvp $gMainPane`;\n\tint    $nPanes = 0;\n\tstring $editorName;\n\tstring $panelName;\n\tstring $itemFilterName;\n\tstring $panelConfig;\n\n\t//\n\t//  get current state of the UI\n\t//\n\tsceneUIReplacement -update $gMainPane;\n\n\t$panelName = `sceneUIReplacement -getNextPanel \"modelPanel\" (localizedPanelLabel(\"Top View\")) `;\n\tif (\"\" != $panelName) {\n\t\t$label = `panel -q -label $panelName`;\n\t\tmodelPanel -edit -l (localizedPanelLabel(\"Top View\")) -mbv $menusOkayInPanels  $panelName;\n"
		+ "\t\t$editorName = $panelName;\n        modelEditor -e \n            -docTag \"RADRENDER\" \n            -editorChanged \"updateModelPanelBar\" \n            -camera \"|top\" \n            -useInteractiveMode 0\n            -displayLights \"default\" \n            -displayAppearance \"smoothShaded\" \n            -activeOnly 0\n            -ignorePanZoom 0\n            -wireframeOnShaded 0\n            -headsUpDisplay 1\n            -holdOuts 1\n            -selectionHiliteDisplay 1\n            -useDefaultMaterial 0\n            -bufferMode \"double\" \n            -twoSidedLighting 0\n            -backfaceCulling 0\n            -xray 0\n            -jointXray 0\n            -activeComponentsXray 0\n            -displayTextures 0\n            -smoothWireframe 0\n            -lineWidth 1\n            -textureAnisotropic 0\n            -textureHilight 1\n            -textureSampling 2\n            -textureDisplay \"modulate\" \n            -textureMaxSize 16384\n            -fogging 0\n            -fogSource \"fragment\" \n            -fogMode \"linear\" \n            -fogStart 0\n"
		+ "            -fogEnd 100\n            -fogDensity 0.1\n            -fogColor 0.5 0.5 0.5 1 \n            -depthOfFieldPreview 1\n            -maxConstantTransparency 1\n            -rendererName \"vp2Renderer\" \n            -objectFilterShowInHUD 1\n            -isFiltered 0\n            -colorResolution 256 256 \n            -bumpResolution 512 512 \n            -textureCompression 0\n            -transparencyAlgorithm \"frontAndBackCull\" \n            -transpInShadows 0\n            -cullingOverride \"none\" \n            -lowQualityLighting 0\n            -maximumNumHardwareLights 1\n            -occlusionCulling 0\n            -shadingModel 0\n            -useBaseRenderer 0\n            -useReducedRenderer 0\n            -smallObjectCulling 0\n            -smallObjectThreshold -1 \n            -interactiveDisableShadows 0\n            -interactiveBackFaceCull 0\n            -sortTransparent 1\n            -controllers 1\n            -nurbsCurves 1\n            -nurbsSurfaces 1\n            -polymeshes 1\n            -subdivSurfaces 1\n            -planes 1\n"
		+ "            -lights 1\n            -cameras 1\n            -controlVertices 1\n            -hulls 1\n            -grid 1\n            -imagePlane 1\n            -joints 1\n            -ikHandles 1\n            -deformers 1\n            -dynamics 1\n            -particleInstancers 1\n            -fluids 1\n            -hairSystems 1\n            -follicles 1\n            -nCloths 1\n            -nParticles 1\n            -nRigids 1\n            -dynamicConstraints 1\n            -locators 1\n            -manipulators 1\n            -pluginShapes 1\n            -dimensions 1\n            -handles 1\n            -pivots 1\n            -textures 1\n            -strokes 1\n            -motionTrails 1\n            -clipGhosts 1\n            -greasePencils 1\n            -shadows 0\n            -captureSequenceNumber -1\n            -width 1\n            -height 1\n            -sceneRenderFilter 0\n            -activeShadingGraph \"ballora_animatronic_shadow_rig:rsMaterial1SG,ballora_animatronic_shadow_rig:MAT_ballora,ballora_animatronic_shadow_rig:MAT_ballora\" \n"
		+ "            -activeCustomGeometry \"meshShaderball\" \n            -activeCustomLighSet \"defaultAreaLightSet\" \n            $editorName;\n        modelEditor -e -viewSelected 0 $editorName;\n        modelEditor -e \n            -pluginObjects \"gpuCacheDisplayFilter\" 1 \n            $editorName;\n\t\tif (!$useSceneConfig) {\n\t\t\tpanel -e -l $label $panelName;\n\t\t}\n\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextPanel \"modelPanel\" (localizedPanelLabel(\"Side View\")) `;\n\tif (\"\" != $panelName) {\n\t\t$label = `panel -q -label $panelName`;\n\t\tmodelPanel -edit -l (localizedPanelLabel(\"Side View\")) -mbv $menusOkayInPanels  $panelName;\n\t\t$editorName = $panelName;\n        modelEditor -e \n            -docTag \"RADRENDER\" \n            -editorChanged \"updateModelPanelBar\" \n            -camera \"|side\" \n            -useInteractiveMode 0\n            -displayLights \"default\" \n            -displayAppearance \"smoothShaded\" \n            -activeOnly 0\n            -ignorePanZoom 0\n            -wireframeOnShaded 0\n            -headsUpDisplay 1\n            -holdOuts 1\n"
		+ "            -selectionHiliteDisplay 1\n            -useDefaultMaterial 0\n            -bufferMode \"double\" \n            -twoSidedLighting 0\n            -backfaceCulling 0\n            -xray 0\n            -jointXray 0\n            -activeComponentsXray 0\n            -displayTextures 0\n            -smoothWireframe 0\n            -lineWidth 1\n            -textureAnisotropic 0\n            -textureHilight 1\n            -textureSampling 2\n            -textureDisplay \"modulate\" \n            -textureMaxSize 16384\n            -fogging 0\n            -fogSource \"fragment\" \n            -fogMode \"linear\" \n            -fogStart 0\n            -fogEnd 100\n            -fogDensity 0.1\n            -fogColor 0.5 0.5 0.5 1 \n            -depthOfFieldPreview 1\n            -maxConstantTransparency 1\n            -rendererName \"vp2Renderer\" \n            -objectFilterShowInHUD 1\n            -isFiltered 0\n            -colorResolution 256 256 \n            -bumpResolution 512 512 \n            -textureCompression 0\n            -transparencyAlgorithm \"frontAndBackCull\" \n"
		+ "            -transpInShadows 0\n            -cullingOverride \"none\" \n            -lowQualityLighting 0\n            -maximumNumHardwareLights 1\n            -occlusionCulling 0\n            -shadingModel 0\n            -useBaseRenderer 0\n            -useReducedRenderer 0\n            -smallObjectCulling 0\n            -smallObjectThreshold -1 \n            -interactiveDisableShadows 0\n            -interactiveBackFaceCull 0\n            -sortTransparent 1\n            -controllers 1\n            -nurbsCurves 1\n            -nurbsSurfaces 1\n            -polymeshes 1\n            -subdivSurfaces 1\n            -planes 1\n            -lights 1\n            -cameras 1\n            -controlVertices 1\n            -hulls 1\n            -grid 1\n            -imagePlane 1\n            -joints 1\n            -ikHandles 1\n            -deformers 1\n            -dynamics 1\n            -particleInstancers 1\n            -fluids 1\n            -hairSystems 1\n            -follicles 1\n            -nCloths 1\n            -nParticles 1\n            -nRigids 1\n"
		+ "            -dynamicConstraints 1\n            -locators 1\n            -manipulators 1\n            -pluginShapes 1\n            -dimensions 1\n            -handles 1\n            -pivots 1\n            -textures 1\n            -strokes 1\n            -motionTrails 1\n            -clipGhosts 1\n            -greasePencils 1\n            -shadows 0\n            -captureSequenceNumber -1\n            -width 1\n            -height 1\n            -sceneRenderFilter 0\n            -activeShadingGraph \"ballora_animatronic_shadow_rig:rsMaterial1SG,ballora_animatronic_shadow_rig:MAT_ballora,ballora_animatronic_shadow_rig:MAT_ballora\" \n            -activeCustomGeometry \"meshShaderball\" \n            -activeCustomLighSet \"defaultAreaLightSet\" \n            $editorName;\n        modelEditor -e -viewSelected 0 $editorName;\n        modelEditor -e \n            -pluginObjects \"gpuCacheDisplayFilter\" 1 \n            $editorName;\n\t\tif (!$useSceneConfig) {\n\t\t\tpanel -e -l $label $panelName;\n\t\t}\n\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextPanel \"modelPanel\" (localizedPanelLabel(\"Front View\")) `;\n"
		+ "\tif (\"\" != $panelName) {\n\t\t$label = `panel -q -label $panelName`;\n\t\tmodelPanel -edit -l (localizedPanelLabel(\"Front View\")) -mbv $menusOkayInPanels  $panelName;\n\t\t$editorName = $panelName;\n        modelEditor -e \n            -docTag \"RADRENDER\" \n            -editorChanged \"updateModelPanelBar\" \n            -camera \"|front\" \n            -useInteractiveMode 0\n            -displayLights \"default\" \n            -displayAppearance \"smoothShaded\" \n            -activeOnly 0\n            -ignorePanZoom 0\n            -wireframeOnShaded 0\n            -headsUpDisplay 1\n            -holdOuts 1\n            -selectionHiliteDisplay 1\n            -useDefaultMaterial 0\n            -bufferMode \"double\" \n            -twoSidedLighting 0\n            -backfaceCulling 0\n            -xray 0\n            -jointXray 0\n            -activeComponentsXray 0\n            -displayTextures 0\n            -smoothWireframe 0\n            -lineWidth 1\n            -textureAnisotropic 0\n            -textureHilight 1\n            -textureSampling 2\n            -textureDisplay \"modulate\" \n"
		+ "            -textureMaxSize 16384\n            -fogging 0\n            -fogSource \"fragment\" \n            -fogMode \"linear\" \n            -fogStart 0\n            -fogEnd 100\n            -fogDensity 0.1\n            -fogColor 0.5 0.5 0.5 1 \n            -depthOfFieldPreview 1\n            -maxConstantTransparency 1\n            -rendererName \"vp2Renderer\" \n            -objectFilterShowInHUD 1\n            -isFiltered 0\n            -colorResolution 256 256 \n            -bumpResolution 512 512 \n            -textureCompression 0\n            -transparencyAlgorithm \"frontAndBackCull\" \n            -transpInShadows 0\n            -cullingOverride \"none\" \n            -lowQualityLighting 0\n            -maximumNumHardwareLights 1\n            -occlusionCulling 0\n            -shadingModel 0\n            -useBaseRenderer 0\n            -useReducedRenderer 0\n            -smallObjectCulling 0\n            -smallObjectThreshold -1 \n            -interactiveDisableShadows 0\n            -interactiveBackFaceCull 0\n            -sortTransparent 1\n"
		+ "            -controllers 1\n            -nurbsCurves 1\n            -nurbsSurfaces 1\n            -polymeshes 1\n            -subdivSurfaces 1\n            -planes 1\n            -lights 1\n            -cameras 1\n            -controlVertices 1\n            -hulls 1\n            -grid 1\n            -imagePlane 1\n            -joints 1\n            -ikHandles 1\n            -deformers 1\n            -dynamics 1\n            -particleInstancers 1\n            -fluids 1\n            -hairSystems 1\n            -follicles 1\n            -nCloths 1\n            -nParticles 1\n            -nRigids 1\n            -dynamicConstraints 1\n            -locators 1\n            -manipulators 1\n            -pluginShapes 1\n            -dimensions 1\n            -handles 1\n            -pivots 1\n            -textures 1\n            -strokes 1\n            -motionTrails 1\n            -clipGhosts 1\n            -greasePencils 1\n            -shadows 0\n            -captureSequenceNumber -1\n            -width 1\n            -height 1\n            -sceneRenderFilter 0\n"
		+ "            -activeShadingGraph \"ballora_animatronic_shadow_rig:rsMaterial1SG,ballora_animatronic_shadow_rig:MAT_ballora,ballora_animatronic_shadow_rig:MAT_ballora\" \n            -activeCustomGeometry \"meshShaderball\" \n            -activeCustomLighSet \"defaultAreaLightSet\" \n            $editorName;\n        modelEditor -e -viewSelected 0 $editorName;\n        modelEditor -e \n            -pluginObjects \"gpuCacheDisplayFilter\" 1 \n            $editorName;\n\t\tif (!$useSceneConfig) {\n\t\t\tpanel -e -l $label $panelName;\n\t\t}\n\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextPanel \"modelPanel\" (localizedPanelLabel(\"Persp View\")) `;\n\tif (\"\" != $panelName) {\n\t\t$label = `panel -q -label $panelName`;\n\t\tmodelPanel -edit -l (localizedPanelLabel(\"Persp View\")) -mbv $menusOkayInPanels  $panelName;\n\t\t$editorName = $panelName;\n        modelEditor -e \n            -docTag \"RADRENDER\" \n            -editorChanged \"updateModelPanelBar\" \n            -camera \"|persp\" \n            -useInteractiveMode 0\n            -displayLights \"default\" \n            -displayAppearance \"smoothShaded\" \n"
		+ "            -activeOnly 0\n            -ignorePanZoom 0\n            -wireframeOnShaded 0\n            -headsUpDisplay 1\n            -holdOuts 1\n            -selectionHiliteDisplay 1\n            -useDefaultMaterial 0\n            -bufferMode \"double\" \n            -twoSidedLighting 0\n            -backfaceCulling 0\n            -xray 0\n            -jointXray 0\n            -activeComponentsXray 0\n            -displayTextures 0\n            -smoothWireframe 0\n            -lineWidth 1\n            -textureAnisotropic 0\n            -textureHilight 1\n            -textureSampling 2\n            -textureDisplay \"modulate\" \n            -textureMaxSize 16384\n            -fogging 0\n            -fogSource \"fragment\" \n            -fogMode \"linear\" \n            -fogStart 0\n            -fogEnd 100\n            -fogDensity 0.1\n            -fogColor 0.5 0.5 0.5 1 \n            -depthOfFieldPreview 1\n            -maxConstantTransparency 1\n            -rendererName \"vp2Renderer\" \n            -objectFilterShowInHUD 1\n            -isFiltered 0\n"
		+ "            -colorResolution 256 256 \n            -bumpResolution 512 512 \n            -textureCompression 0\n            -transparencyAlgorithm \"frontAndBackCull\" \n            -transpInShadows 0\n            -cullingOverride \"none\" \n            -lowQualityLighting 0\n            -maximumNumHardwareLights 1\n            -occlusionCulling 0\n            -shadingModel 0\n            -useBaseRenderer 0\n            -useReducedRenderer 0\n            -smallObjectCulling 0\n            -smallObjectThreshold -1 \n            -interactiveDisableShadows 0\n            -interactiveBackFaceCull 0\n            -sortTransparent 1\n            -controllers 1\n            -nurbsCurves 1\n            -nurbsSurfaces 1\n            -polymeshes 1\n            -subdivSurfaces 1\n            -planes 1\n            -lights 1\n            -cameras 1\n            -controlVertices 1\n            -hulls 1\n            -grid 1\n            -imagePlane 1\n            -joints 1\n            -ikHandles 1\n            -deformers 1\n            -dynamics 1\n            -particleInstancers 1\n"
		+ "            -fluids 1\n            -hairSystems 1\n            -follicles 1\n            -nCloths 1\n            -nParticles 1\n            -nRigids 1\n            -dynamicConstraints 1\n            -locators 1\n            -manipulators 1\n            -pluginShapes 1\n            -dimensions 1\n            -handles 1\n            -pivots 1\n            -textures 1\n            -strokes 1\n            -motionTrails 1\n            -clipGhosts 1\n            -greasePencils 1\n            -shadows 0\n            -captureSequenceNumber -1\n            -width 1050\n            -height 744\n            -sceneRenderFilter 0\n            -activeShadingGraph \"ballora_animatronic_shadow_rig:rsMaterial1SG,ballora_animatronic_shadow_rig:MAT_ballora,ballora_animatronic_shadow_rig:MAT_ballora\" \n            -activeCustomGeometry \"meshShaderball\" \n            $editorName;\n        modelEditor -e -viewSelected 0 $editorName;\n        modelEditor -e \n            -pluginObjects \"gpuCacheDisplayFilter\" 1 \n            $editorName;\n\t\tif (!$useSceneConfig) {\n"
		+ "\t\t\tpanel -e -l $label $panelName;\n\t\t}\n\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextPanel \"outlinerPanel\" (localizedPanelLabel(\"Outliner\")) `;\n\tif (\"\" != $panelName) {\n\t\t$label = `panel -q -label $panelName`;\n\t\toutlinerPanel -edit -l (localizedPanelLabel(\"Outliner\")) -mbv $menusOkayInPanels  $panelName;\n\t\t$editorName = $panelName;\n        outlinerEditor -e \n            -docTag \"isolOutln_fromSeln\" \n            -showShapes 0\n            -showAssignedMaterials 0\n            -showTimeEditor 1\n            -showReferenceNodes 0\n            -showReferenceMembers 0\n            -showAttributes 0\n            -showConnected 0\n            -showAnimCurvesOnly 0\n            -showMuteInfo 0\n            -organizeByLayer 1\n            -organizeByClip 1\n            -showAnimLayerWeight 1\n            -autoExpandLayers 1\n            -autoExpand 0\n            -showDagOnly 1\n            -showAssets 1\n            -showContainedOnly 1\n            -showPublishedAsConnected 0\n            -showParentContainers 0\n            -showContainerContents 1\n"
		+ "            -ignoreDagHierarchy 0\n            -expandConnections 0\n            -showUpstreamCurves 1\n            -showUnitlessCurves 1\n            -showCompounds 1\n            -showLeafs 1\n            -showNumericAttrsOnly 0\n            -highlightActive 1\n            -autoSelectNewObjects 0\n            -doNotSelectNewObjects 0\n            -dropIsParent 1\n            -transmitFilters 0\n            -setFilter \"defaultSetFilter\" \n            -showSetMembers 1\n            -allowMultiSelection 1\n            -alwaysToggleSelect 0\n            -directSelect 0\n            -isSet 0\n            -isSetMember 0\n            -displayMode \"DAG\" \n            -expandObjects 0\n            -setsIgnoreFilters 1\n            -containersIgnoreFilters 0\n            -editAttrName 0\n            -showAttrValues 0\n            -highlightSecondary 0\n            -showUVAttrsOnly 0\n            -showTextureNodesOnly 0\n            -attrAlphaOrder \"default\" \n            -animLayerFilterOptions \"allAffecting\" \n            -sortOrder \"none\" \n            -longNames 0\n"
		+ "            -niceNames 1\n            -showNamespace 1\n            -showPinIcons 0\n            -mapMotionTrails 0\n            -ignoreHiddenAttribute 0\n            -ignoreOutlinerColor 0\n            -renderFilterVisible 0\n            -renderFilterIndex 0\n            -selectionOrder \"chronological\" \n            -expandAttribute 0\n            $editorName;\n\t\tif (!$useSceneConfig) {\n\t\t\tpanel -e -l $label $panelName;\n\t\t}\n\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextPanel \"outlinerPanel\" (localizedPanelLabel(\"Outliner\")) `;\n\tif (\"\" != $panelName) {\n\t\t$label = `panel -q -label $panelName`;\n\t\toutlinerPanel -edit -l (localizedPanelLabel(\"Outliner\")) -mbv $menusOkayInPanels  $panelName;\n\t\t$editorName = $panelName;\n        outlinerEditor -e \n            -docTag \"isolOutln_fromSeln\" \n            -showShapes 0\n            -showAssignedMaterials 0\n            -showTimeEditor 1\n            -showReferenceNodes 0\n            -showReferenceMembers 0\n            -showAttributes 0\n            -showConnected 0\n            -showAnimCurvesOnly 0\n"
		+ "            -showMuteInfo 0\n            -organizeByLayer 1\n            -organizeByClip 1\n            -showAnimLayerWeight 1\n            -autoExpandLayers 1\n            -autoExpand 0\n            -showDagOnly 1\n            -showAssets 1\n            -showContainedOnly 1\n            -showPublishedAsConnected 0\n            -showParentContainers 0\n            -showContainerContents 1\n            -ignoreDagHierarchy 0\n            -expandConnections 0\n            -showUpstreamCurves 1\n            -showUnitlessCurves 1\n            -showCompounds 1\n            -showLeafs 1\n            -showNumericAttrsOnly 0\n            -highlightActive 1\n            -autoSelectNewObjects 0\n            -doNotSelectNewObjects 0\n            -dropIsParent 1\n            -transmitFilters 0\n            -setFilter \"defaultSetFilter\" \n            -showSetMembers 1\n            -allowMultiSelection 1\n            -alwaysToggleSelect 0\n            -directSelect 0\n            -displayMode \"DAG\" \n            -expandObjects 0\n            -setsIgnoreFilters 1\n"
		+ "            -containersIgnoreFilters 0\n            -editAttrName 0\n            -showAttrValues 0\n            -highlightSecondary 0\n            -showUVAttrsOnly 0\n            -showTextureNodesOnly 0\n            -attrAlphaOrder \"default\" \n            -animLayerFilterOptions \"allAffecting\" \n            -sortOrder \"none\" \n            -longNames 0\n            -niceNames 1\n            -showNamespace 1\n            -showPinIcons 0\n            -mapMotionTrails 0\n            -ignoreHiddenAttribute 0\n            -ignoreOutlinerColor 0\n            -renderFilterVisible 0\n            $editorName;\n\t\tif (!$useSceneConfig) {\n\t\t\tpanel -e -l $label $panelName;\n\t\t}\n\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextScriptedPanel \"graphEditor\" (localizedPanelLabel(\"Graph Editor\")) `;\n\tif (\"\" != $panelName) {\n\t\t$label = `panel -q -label $panelName`;\n\t\tscriptedPanel -edit -l (localizedPanelLabel(\"Graph Editor\")) -mbv $menusOkayInPanels  $panelName;\n\n\t\t\t$editorName = ($panelName+\"OutlineEd\");\n            outlinerEditor -e \n                -showShapes 1\n"
		+ "                -showAssignedMaterials 0\n                -showTimeEditor 1\n                -showReferenceNodes 0\n                -showReferenceMembers 0\n                -showAttributes 1\n                -showConnected 1\n                -showAnimCurvesOnly 1\n                -showMuteInfo 0\n                -organizeByLayer 1\n                -organizeByClip 1\n                -showAnimLayerWeight 1\n                -autoExpandLayers 1\n                -autoExpand 1\n                -showDagOnly 0\n                -showAssets 1\n                -showContainedOnly 0\n                -showPublishedAsConnected 0\n                -showParentContainers 0\n                -showContainerContents 0\n                -ignoreDagHierarchy 0\n                -expandConnections 1\n                -showUpstreamCurves 1\n                -showUnitlessCurves 1\n                -showCompounds 0\n                -showLeafs 1\n                -showNumericAttrsOnly 1\n                -highlightActive 0\n                -autoSelectNewObjects 1\n                -doNotSelectNewObjects 0\n"
		+ "                -dropIsParent 1\n                -transmitFilters 1\n                -setFilter \"0\" \n                -showSetMembers 0\n                -allowMultiSelection 1\n                -alwaysToggleSelect 0\n                -directSelect 0\n                -displayMode \"DAG\" \n                -expandObjects 0\n                -setsIgnoreFilters 1\n                -containersIgnoreFilters 0\n                -editAttrName 0\n                -showAttrValues 0\n                -highlightSecondary 0\n                -showUVAttrsOnly 0\n                -showTextureNodesOnly 0\n                -attrAlphaOrder \"default\" \n                -animLayerFilterOptions \"allAffecting\" \n                -sortOrder \"none\" \n                -longNames 0\n                -niceNames 1\n                -showNamespace 1\n                -showPinIcons 1\n                -mapMotionTrails 1\n                -ignoreHiddenAttribute 0\n                -ignoreOutlinerColor 0\n                -renderFilterVisible 0\n                $editorName;\n\n\t\t\t$editorName = ($panelName+\"GraphEd\");\n"
		+ "            animCurveEditor -e \n                -displayValues 0\n                -snapTime \"integer\" \n                -snapValue \"none\" \n                -showPlayRangeShades \"on\" \n                -lockPlayRangeShades \"off\" \n                -smoothness \"fine\" \n                -resultSamples 1\n                -resultScreenSamples 0\n                -resultUpdate \"delayed\" \n                -showUpstreamCurves 1\n                -keyMinScale 1\n                -stackedCurvesMin -1\n                -stackedCurvesMax 1\n                -stackedCurvesSpace 0.2\n                -preSelectionHighlight 0\n                -constrainDrag 0\n                -valueLinesToggle 1\n                -outliner \"graphEditor1OutlineEd\" \n                -highlightAffectedCurves 0\n                $editorName;\n\t\tif (!$useSceneConfig) {\n\t\t\tpanel -e -l $label $panelName;\n\t\t}\n\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextScriptedPanel \"dopeSheetPanel\" (localizedPanelLabel(\"Dope Sheet\")) `;\n\tif (\"\" != $panelName) {\n\t\t$label = `panel -q -label $panelName`;\n"
		+ "\t\tscriptedPanel -edit -l (localizedPanelLabel(\"Dope Sheet\")) -mbv $menusOkayInPanels  $panelName;\n\n\t\t\t$editorName = ($panelName+\"OutlineEd\");\n            outlinerEditor -e \n                -showShapes 1\n                -showAssignedMaterials 0\n                -showTimeEditor 1\n                -showReferenceNodes 0\n                -showReferenceMembers 0\n                -showAttributes 1\n                -showConnected 1\n                -showAnimCurvesOnly 1\n                -showMuteInfo 0\n                -organizeByLayer 1\n                -organizeByClip 1\n                -showAnimLayerWeight 1\n                -autoExpandLayers 1\n                -autoExpand 0\n                -showDagOnly 0\n                -showAssets 1\n                -showContainedOnly 0\n                -showPublishedAsConnected 0\n                -showParentContainers 0\n                -showContainerContents 0\n                -ignoreDagHierarchy 0\n                -expandConnections 1\n                -showUpstreamCurves 1\n                -showUnitlessCurves 0\n"
		+ "                -showCompounds 1\n                -showLeafs 1\n                -showNumericAttrsOnly 1\n                -highlightActive 0\n                -autoSelectNewObjects 0\n                -doNotSelectNewObjects 1\n                -dropIsParent 1\n                -transmitFilters 0\n                -setFilter \"0\" \n                -showSetMembers 0\n                -allowMultiSelection 1\n                -alwaysToggleSelect 0\n                -directSelect 0\n                -displayMode \"DAG\" \n                -expandObjects 0\n                -setsIgnoreFilters 1\n                -containersIgnoreFilters 0\n                -editAttrName 0\n                -showAttrValues 0\n                -highlightSecondary 0\n                -showUVAttrsOnly 0\n                -showTextureNodesOnly 0\n                -attrAlphaOrder \"default\" \n                -animLayerFilterOptions \"allAffecting\" \n                -sortOrder \"none\" \n                -longNames 0\n                -niceNames 1\n                -showNamespace 1\n                -showPinIcons 0\n"
		+ "                -mapMotionTrails 1\n                -ignoreHiddenAttribute 0\n                -ignoreOutlinerColor 0\n                -renderFilterVisible 0\n                $editorName;\n\n\t\t\t$editorName = ($panelName+\"DopeSheetEd\");\n            dopeSheetEditor -e \n                -displayValues 0\n                -snapTime \"integer\" \n                -snapValue \"none\" \n                -outliner \"dopeSheetPanel1OutlineEd\" \n                -showSummary 1\n                -showScene 0\n                -hierarchyBelow 0\n                -showTicks 1\n                -selectionWindow 0 0 0 0 \n                $editorName;\n\t\tif (!$useSceneConfig) {\n\t\t\tpanel -e -l $label $panelName;\n\t\t}\n\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextScriptedPanel \"timeEditorPanel\" (localizedPanelLabel(\"Time Editor\")) `;\n\tif (\"\" != $panelName) {\n\t\t$label = `panel -q -label $panelName`;\n\t\tscriptedPanel -edit -l (localizedPanelLabel(\"Time Editor\")) -mbv $menusOkayInPanels  $panelName;\n\t\tif (!$useSceneConfig) {\n\t\t\tpanel -e -l $label $panelName;\n\t\t}\n"
		+ "\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextScriptedPanel \"clipEditorPanel\" (localizedPanelLabel(\"Trax Editor\")) `;\n\tif (\"\" != $panelName) {\n\t\t$label = `panel -q -label $panelName`;\n\t\tscriptedPanel -edit -l (localizedPanelLabel(\"Trax Editor\")) -mbv $menusOkayInPanels  $panelName;\n\n\t\t\t$editorName = clipEditorNameFromPanel($panelName);\n            clipEditor -e \n                -displayValues 0\n                -snapTime \"none\" \n                -snapValue \"none\" \n                -initialized 0\n                -manageSequencer 0 \n                $editorName;\n\t\tif (!$useSceneConfig) {\n\t\t\tpanel -e -l $label $panelName;\n\t\t}\n\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextScriptedPanel \"sequenceEditorPanel\" (localizedPanelLabel(\"Camera Sequencer\")) `;\n\tif (\"\" != $panelName) {\n\t\t$label = `panel -q -label $panelName`;\n\t\tscriptedPanel -edit -l (localizedPanelLabel(\"Camera Sequencer\")) -mbv $menusOkayInPanels  $panelName;\n\n\t\t\t$editorName = sequenceEditorNameFromPanel($panelName);\n            clipEditor -e \n                -displayValues 0\n"
		+ "                -snapTime \"none\" \n                -snapValue \"none\" \n                -initialized 0\n                -manageSequencer 1 \n                $editorName;\n\t\tif (!$useSceneConfig) {\n\t\t\tpanel -e -l $label $panelName;\n\t\t}\n\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextScriptedPanel \"hyperGraphPanel\" (localizedPanelLabel(\"Hypergraph Hierarchy\")) `;\n\tif (\"\" != $panelName) {\n\t\t$label = `panel -q -label $panelName`;\n\t\tscriptedPanel -edit -l (localizedPanelLabel(\"Hypergraph Hierarchy\")) -mbv $menusOkayInPanels  $panelName;\n\n\t\t\t$editorName = ($panelName+\"HyperGraphEd\");\n            hyperGraph -e \n                -graphLayoutStyle \"hierarchicalLayout\" \n                -orientation \"horiz\" \n                -mergeConnections 0\n                -zoom 1\n                -animateTransition 0\n                -showRelationships 1\n                -showShapes 0\n                -showDeformers 0\n                -showExpressions 0\n                -showConstraints 0\n                -showConnectionFromSelected 0\n                -showConnectionToSelected 0\n"
		+ "                -showConstraintLabels 0\n                -showUnderworld 0\n                -showInvisible 0\n                -transitionFrames 1\n                -opaqueContainers 0\n                -freeform 0\n                -image \"C:/work/Batman/characters/Bane/sourceimages/Bane_tpage_2048.tga\" \n                -imagePosition 0 0 \n                -imageScale 1\n                -imageEnabled 0\n                -graphType \"DAG\" \n                -heatMapDisplay 0\n                -updateSelection 1\n                -updateNodeAdded 1\n                -useDrawOverrideColor 0\n                -limitGraphTraversal -1\n                -range 0 0 \n                -iconSize \"smallIcons\" \n                -showCachedConnections 0\n                $editorName;\n\t\tif (!$useSceneConfig) {\n\t\t\tpanel -e -l $label $panelName;\n\t\t}\n\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextScriptedPanel \"hyperShadePanel\" (localizedPanelLabel(\"Hypershade\")) `;\n\tif (\"\" != $panelName) {\n\t\t$label = `panel -q -label $panelName`;\n\t\tscriptedPanel -edit -l (localizedPanelLabel(\"Hypershade\")) -mbv $menusOkayInPanels  $panelName;\n"
		+ "\t\tif (!$useSceneConfig) {\n\t\t\tpanel -e -l $label $panelName;\n\t\t}\n\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextScriptedPanel \"visorPanel\" (localizedPanelLabel(\"Visor\")) `;\n\tif (\"\" != $panelName) {\n\t\t$label = `panel -q -label $panelName`;\n\t\tscriptedPanel -edit -l (localizedPanelLabel(\"Visor\")) -mbv $menusOkayInPanels  $panelName;\n\t\tif (!$useSceneConfig) {\n\t\t\tpanel -e -l $label $panelName;\n\t\t}\n\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextScriptedPanel \"nodeEditorPanel\" (localizedPanelLabel(\"Node Editor\")) `;\n\tif ($nodeEditorPanelVisible || $nodeEditorWorkspaceControlOpen) {\n\t\tif (\"\" == $panelName) {\n\t\t\tif ($useSceneConfig) {\n\t\t\t\t$panelName = `scriptedPanel -unParent  -type \"nodeEditorPanel\" -l (localizedPanelLabel(\"Node Editor\")) -mbv $menusOkayInPanels `;\n\n\t\t\t$editorName = ($panelName+\"NodeEditorEd\");\n            nodeEditor -e \n                -allAttributes 0\n                -allNodes 0\n                -autoSizeNodes 1\n                -consistentNameSize 1\n                -createNodeCommand \"nodeEdCreateNodeCommand\" \n"
		+ "                -connectNodeOnCreation 0\n                -connectOnDrop 0\n                -copyConnectionsOnPaste 0\n                -connectionStyle \"bezier\" \n                -defaultPinnedState 0\n                -additiveGraphingMode 0\n                -settingsChangedCallback \"nodeEdSyncControls\" \n                -traversalDepthLimit -1\n                -keyPressCommand \"nodeEdKeyPressCommand\" \n                -nodeTitleMode \"name\" \n                -gridSnap 0\n                -gridVisibility 1\n                -crosshairOnEdgeDragging 0\n                -popupMenuScript \"nodeEdBuildPanelMenus\" \n                -showNamespace 1\n                -showShapes 1\n                -showSGShapes 0\n                -showTransforms 1\n                -useAssets 1\n                -syncedSelection 1\n                -extendToShapes 1\n                -editorMode \"default\" \n                -hasWatchpoint 0\n                $editorName;\n\t\t\t}\n\t\t} else {\n\t\t\t$label = `panel -q -label $panelName`;\n\t\t\tscriptedPanel -edit -l (localizedPanelLabel(\"Node Editor\")) -mbv $menusOkayInPanels  $panelName;\n"
		+ "\n\t\t\t$editorName = ($panelName+\"NodeEditorEd\");\n            nodeEditor -e \n                -allAttributes 0\n                -allNodes 0\n                -autoSizeNodes 1\n                -consistentNameSize 1\n                -createNodeCommand \"nodeEdCreateNodeCommand\" \n                -connectNodeOnCreation 0\n                -connectOnDrop 0\n                -copyConnectionsOnPaste 0\n                -connectionStyle \"bezier\" \n                -defaultPinnedState 0\n                -additiveGraphingMode 0\n                -settingsChangedCallback \"nodeEdSyncControls\" \n                -traversalDepthLimit -1\n                -keyPressCommand \"nodeEdKeyPressCommand\" \n                -nodeTitleMode \"name\" \n                -gridSnap 0\n                -gridVisibility 1\n                -crosshairOnEdgeDragging 0\n                -popupMenuScript \"nodeEdBuildPanelMenus\" \n                -showNamespace 1\n                -showShapes 1\n                -showSGShapes 0\n                -showTransforms 1\n                -useAssets 1\n"
		+ "                -syncedSelection 1\n                -extendToShapes 1\n                -editorMode \"default\" \n                -hasWatchpoint 0\n                $editorName;\n\t\t\tif (!$useSceneConfig) {\n\t\t\t\tpanel -e -l $label $panelName;\n\t\t\t}\n\t\t}\n\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextScriptedPanel \"createNodePanel\" (localizedPanelLabel(\"Create Node\")) `;\n\tif (\"\" != $panelName) {\n\t\t$label = `panel -q -label $panelName`;\n\t\tscriptedPanel -edit -l (localizedPanelLabel(\"Create Node\")) -mbv $menusOkayInPanels  $panelName;\n\t\tif (!$useSceneConfig) {\n\t\t\tpanel -e -l $label $panelName;\n\t\t}\n\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextScriptedPanel \"polyTexturePlacementPanel\" (localizedPanelLabel(\"UV Editor\")) `;\n\tif (\"\" != $panelName) {\n\t\t$label = `panel -q -label $panelName`;\n\t\tscriptedPanel -edit -l (localizedPanelLabel(\"UV Editor\")) -mbv $menusOkayInPanels  $panelName;\n\t\tif (!$useSceneConfig) {\n\t\t\tpanel -e -l $label $panelName;\n\t\t}\n\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextScriptedPanel \"renderWindowPanel\" (localizedPanelLabel(\"Render View\")) `;\n"
		+ "\tif (\"\" != $panelName) {\n\t\t$label = `panel -q -label $panelName`;\n\t\tscriptedPanel -edit -l (localizedPanelLabel(\"Render View\")) -mbv $menusOkayInPanels  $panelName;\n\t\tif (!$useSceneConfig) {\n\t\t\tpanel -e -l $label $panelName;\n\t\t}\n\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextPanel \"shapePanel\" (localizedPanelLabel(\"Shape Editor\")) `;\n\tif (\"\" != $panelName) {\n\t\t$label = `panel -q -label $panelName`;\n\t\tshapePanel -edit -l (localizedPanelLabel(\"Shape Editor\")) -mbv $menusOkayInPanels  $panelName;\n\t\tif (!$useSceneConfig) {\n\t\t\tpanel -e -l $label $panelName;\n\t\t}\n\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextPanel \"posePanel\" (localizedPanelLabel(\"Pose Editor\")) `;\n\tif (\"\" != $panelName) {\n\t\t$label = `panel -q -label $panelName`;\n\t\tposePanel -edit -l (localizedPanelLabel(\"Pose Editor\")) -mbv $menusOkayInPanels  $panelName;\n\t\tif (!$useSceneConfig) {\n\t\t\tpanel -e -l $label $panelName;\n\t\t}\n\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextScriptedPanel \"dynRelEdPanel\" (localizedPanelLabel(\"Dynamic Relationships\")) `;\n\tif (\"\" != $panelName) {\n"
		+ "\t\t$label = `panel -q -label $panelName`;\n\t\tscriptedPanel -edit -l (localizedPanelLabel(\"Dynamic Relationships\")) -mbv $menusOkayInPanels  $panelName;\n\t\tif (!$useSceneConfig) {\n\t\t\tpanel -e -l $label $panelName;\n\t\t}\n\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextScriptedPanel \"relationshipPanel\" (localizedPanelLabel(\"Relationship Editor\")) `;\n\tif (\"\" != $panelName) {\n\t\t$label = `panel -q -label $panelName`;\n\t\tscriptedPanel -edit -l (localizedPanelLabel(\"Relationship Editor\")) -mbv $menusOkayInPanels  $panelName;\n\t\tif (!$useSceneConfig) {\n\t\t\tpanel -e -l $label $panelName;\n\t\t}\n\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextScriptedPanel \"referenceEditorPanel\" (localizedPanelLabel(\"Reference Editor\")) `;\n\tif (\"\" != $panelName) {\n\t\t$label = `panel -q -label $panelName`;\n\t\tscriptedPanel -edit -l (localizedPanelLabel(\"Reference Editor\")) -mbv $menusOkayInPanels  $panelName;\n\t\tif (!$useSceneConfig) {\n\t\t\tpanel -e -l $label $panelName;\n\t\t}\n\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextScriptedPanel \"componentEditorPanel\" (localizedPanelLabel(\"Component Editor\")) `;\n"
		+ "\tif (\"\" != $panelName) {\n\t\t$label = `panel -q -label $panelName`;\n\t\tscriptedPanel -edit -l (localizedPanelLabel(\"Component Editor\")) -mbv $menusOkayInPanels  $panelName;\n\t\tif (!$useSceneConfig) {\n\t\t\tpanel -e -l $label $panelName;\n\t\t}\n\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextScriptedPanel \"dynPaintScriptedPanelType\" (localizedPanelLabel(\"Paint Effects\")) `;\n\tif (\"\" != $panelName) {\n\t\t$label = `panel -q -label $panelName`;\n\t\tscriptedPanel -edit -l (localizedPanelLabel(\"Paint Effects\")) -mbv $menusOkayInPanels  $panelName;\n\t\tif (!$useSceneConfig) {\n\t\t\tpanel -e -l $label $panelName;\n\t\t}\n\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextScriptedPanel \"scriptEditorPanel\" (localizedPanelLabel(\"Script Editor\")) `;\n\tif (\"\" != $panelName) {\n\t\t$label = `panel -q -label $panelName`;\n\t\tscriptedPanel -edit -l (localizedPanelLabel(\"Script Editor\")) -mbv $menusOkayInPanels  $panelName;\n\t\tif (!$useSceneConfig) {\n\t\t\tpanel -e -l $label $panelName;\n\t\t}\n\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextScriptedPanel \"profilerPanel\" (localizedPanelLabel(\"Profiler Tool\")) `;\n"
		+ "\tif (\"\" != $panelName) {\n\t\t$label = `panel -q -label $panelName`;\n\t\tscriptedPanel -edit -l (localizedPanelLabel(\"Profiler Tool\")) -mbv $menusOkayInPanels  $panelName;\n\t\tif (!$useSceneConfig) {\n\t\t\tpanel -e -l $label $panelName;\n\t\t}\n\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextScriptedPanel \"contentBrowserPanel\" (localizedPanelLabel(\"Content Browser\")) `;\n\tif (\"\" != $panelName) {\n\t\t$label = `panel -q -label $panelName`;\n\t\tscriptedPanel -edit -l (localizedPanelLabel(\"Content Browser\")) -mbv $menusOkayInPanels  $panelName;\n\t\tif (!$useSceneConfig) {\n\t\t\tpanel -e -l $label $panelName;\n\t\t}\n\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextScriptedPanel \"Stereo\" (localizedPanelLabel(\"Stereo\")) `;\n\tif (\"\" != $panelName) {\n\t\t$label = `panel -q -label $panelName`;\n\t\tscriptedPanel -edit -l (localizedPanelLabel(\"Stereo\")) -mbv $menusOkayInPanels  $panelName;\n{ string $editorName = ($panelName+\"Editor\");\n            stereoCameraView -e \n                -editorChanged \"updateModelPanelBar\" \n                -camera \"|persp\" \n                -useInteractiveMode 0\n"
		+ "                -displayLights \"default\" \n                -displayAppearance \"smoothShaded\" \n                -activeOnly 0\n                -ignorePanZoom 0\n                -wireframeOnShaded 0\n                -headsUpDisplay 1\n                -holdOuts 1\n                -selectionHiliteDisplay 1\n                -useDefaultMaterial 0\n                -bufferMode \"double\" \n                -twoSidedLighting 0\n                -backfaceCulling 0\n                -xray 0\n                -jointXray 0\n                -activeComponentsXray 0\n                -displayTextures 0\n                -smoothWireframe 0\n                -lineWidth 1\n                -textureAnisotropic 0\n                -textureHilight 1\n                -textureSampling 2\n                -textureDisplay \"modulate\" \n                -textureMaxSize 16384\n                -fogging 0\n                -fogSource \"fragment\" \n                -fogMode \"linear\" \n                -fogStart 0\n                -fogEnd 100\n                -fogDensity 0.1\n                -fogColor 0.5 0.5 0.5 1 \n"
		+ "                -depthOfFieldPreview 1\n                -maxConstantTransparency 1\n                -rendererOverrideName \"stereoOverrideVP2\" \n                -objectFilterShowInHUD 1\n                -isFiltered 0\n                -colorResolution 4 4 \n                -bumpResolution 4 4 \n                -textureCompression 0\n                -transparencyAlgorithm \"frontAndBackCull\" \n                -transpInShadows 0\n                -cullingOverride \"none\" \n                -lowQualityLighting 0\n                -maximumNumHardwareLights 0\n                -occlusionCulling 0\n                -shadingModel 0\n                -useBaseRenderer 0\n                -useReducedRenderer 0\n                -smallObjectCulling 0\n                -smallObjectThreshold -1 \n                -interactiveDisableShadows 0\n                -interactiveBackFaceCull 0\n                -sortTransparent 1\n                -controllers 1\n                -nurbsCurves 1\n                -nurbsSurfaces 1\n                -polymeshes 1\n                -subdivSurfaces 1\n"
		+ "                -planes 1\n                -lights 1\n                -cameras 1\n                -controlVertices 1\n                -hulls 1\n                -grid 1\n                -imagePlane 1\n                -joints 1\n                -ikHandles 1\n                -deformers 1\n                -dynamics 1\n                -particleInstancers 1\n                -fluids 1\n                -hairSystems 1\n                -follicles 1\n                -nCloths 1\n                -nParticles 1\n                -nRigids 1\n                -dynamicConstraints 1\n                -locators 1\n                -manipulators 1\n                -pluginShapes 1\n                -dimensions 1\n                -handles 1\n                -pivots 1\n                -textures 1\n                -strokes 1\n                -motionTrails 1\n                -clipGhosts 1\n                -greasePencils 1\n                -shadows 0\n                -captureSequenceNumber -1\n                -width 0\n                -height 0\n                -sceneRenderFilter 0\n"
		+ "                -displayMode \"centerEye\" \n                -viewColor 0 0 0 1 \n                -useCustomBackground 1\n                $editorName;\n            stereoCameraView -e -viewSelected 0 $editorName;\n            stereoCameraView -e \n                -pluginObjects \"gpuCacheDisplayFilter\" 1 \n                $editorName; };\n\t\tif (!$useSceneConfig) {\n\t\t\tpanel -e -l $label $panelName;\n\t\t}\n\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextPanel \"outlinerPanel\" (localizedPanelLabel(\"ToggledOutliner\")) `;\n\tif (\"\" != $panelName) {\n\t\t$label = `panel -q -label $panelName`;\n\t\toutlinerPanel -edit -l (localizedPanelLabel(\"ToggledOutliner\")) -mbv $menusOkayInPanels  $panelName;\n\t\t$editorName = $panelName;\n        outlinerEditor -e \n            -showShapes 0\n            -showAssignedMaterials 0\n            -showTimeEditor 1\n            -showReferenceNodes 1\n            -showReferenceMembers 1\n            -showAttributes 0\n            -showConnected 0\n            -showAnimCurvesOnly 0\n            -showMuteInfo 0\n            -organizeByLayer 1\n"
		+ "            -organizeByClip 1\n            -showAnimLayerWeight 1\n            -autoExpandLayers 1\n            -autoExpand 0\n            -showDagOnly 1\n            -showAssets 1\n            -showContainedOnly 1\n            -showPublishedAsConnected 0\n            -showParentContainers 0\n            -showContainerContents 1\n            -ignoreDagHierarchy 0\n            -expandConnections 0\n            -showUpstreamCurves 1\n            -showUnitlessCurves 1\n            -showCompounds 1\n            -showLeafs 1\n            -showNumericAttrsOnly 0\n            -highlightActive 1\n            -autoSelectNewObjects 0\n            -doNotSelectNewObjects 0\n            -dropIsParent 1\n            -transmitFilters 0\n            -setFilter \"defaultSetFilter\" \n            -showSetMembers 1\n            -allowMultiSelection 1\n            -alwaysToggleSelect 0\n            -directSelect 0\n            -isSet 0\n            -isSetMember 0\n            -displayMode \"DAG\" \n            -expandObjects 0\n            -setsIgnoreFilters 1\n            -containersIgnoreFilters 0\n"
		+ "            -editAttrName 0\n            -showAttrValues 0\n            -highlightSecondary 0\n            -showUVAttrsOnly 0\n            -showTextureNodesOnly 0\n            -attrAlphaOrder \"default\" \n            -animLayerFilterOptions \"allAffecting\" \n            -sortOrder \"none\" \n            -longNames 0\n            -niceNames 1\n            -showNamespace 1\n            -showPinIcons 0\n            -mapMotionTrails 0\n            -ignoreHiddenAttribute 0\n            -ignoreOutlinerColor 0\n            -renderFilterVisible 0\n            -renderFilterIndex 0\n            -selectionOrder \"chronological\" \n            -expandAttribute 0\n            $editorName;\n\t\tif (!$useSceneConfig) {\n\t\t\tpanel -e -l $label $panelName;\n\t\t}\n\t}\n\n\n\tif ($useSceneConfig) {\n        string $configName = `getPanel -cwl (localizedPanelLabel(\"Current Layout\"))`;\n        if (\"\" != $configName) {\n\t\t\tpanelConfiguration -edit -label (localizedPanelLabel(\"Current Layout\")) \n\t\t\t\t-userCreated false\n\t\t\t\t-defaultImage \"vacantCell.xP:/\"\n\t\t\t\t-image \"\"\n\t\t\t\t-sc false\n"
		+ "\t\t\t\t-configString \"global string $gMainPane; paneLayout -e -cn \\\"single\\\" -ps 1 100 100 $gMainPane;\"\n\t\t\t\t-removeAllPanels\n\t\t\t\t-ap false\n\t\t\t\t\t(localizedPanelLabel(\"Persp View\")) \n\t\t\t\t\t\"modelPanel\"\n"
		+ "\t\t\t\t\t\"$panelName = `modelPanel -unParent -l (localizedPanelLabel(\\\"Persp View\\\")) -mbv $menusOkayInPanels `;\\n$editorName = $panelName;\\nmodelEditor -e \\n    -docTag \\\"RADRENDER\\\" \\n    -editorChanged \\\"updateModelPanelBar\\\" \\n    -cam `findStartUpCamera persp` \\n    -useInteractiveMode 0\\n    -displayLights \\\"default\\\" \\n    -displayAppearance \\\"smoothShaded\\\" \\n    -activeOnly 0\\n    -ignorePanZoom 0\\n    -wireframeOnShaded 0\\n    -headsUpDisplay 1\\n    -holdOuts 1\\n    -selectionHiliteDisplay 1\\n    -useDefaultMaterial 0\\n    -bufferMode \\\"double\\\" \\n    -twoSidedLighting 0\\n    -backfaceCulling 0\\n    -xray 0\\n    -jointXray 0\\n    -activeComponentsXray 0\\n    -displayTextures 0\\n    -smoothWireframe 0\\n    -lineWidth 1\\n    -textureAnisotropic 0\\n    -textureHilight 1\\n    -textureSampling 2\\n    -textureDisplay \\\"modulate\\\" \\n    -textureMaxSize 16384\\n    -fogging 0\\n    -fogSource \\\"fragment\\\" \\n    -fogMode \\\"linear\\\" \\n    -fogStart 0\\n    -fogEnd 100\\n    -fogDensity 0.1\\n    -fogColor 0.5 0.5 0.5 1 \\n    -depthOfFieldPreview 1\\n    -maxConstantTransparency 1\\n    -rendererName \\\"vp2Renderer\\\" \\n    -objectFilterShowInHUD 1\\n    -isFiltered 0\\n    -colorResolution 256 256 \\n    -bumpResolution 512 512 \\n    -textureCompression 0\\n    -transparencyAlgorithm \\\"frontAndBackCull\\\" \\n    -transpInShadows 0\\n    -cullingOverride \\\"none\\\" \\n    -lowQualityLighting 0\\n    -maximumNumHardwareLights 1\\n    -occlusionCulling 0\\n    -shadingModel 0\\n    -useBaseRenderer 0\\n    -useReducedRenderer 0\\n    -smallObjectCulling 0\\n    -smallObjectThreshold -1 \\n    -interactiveDisableShadows 0\\n    -interactiveBackFaceCull 0\\n    -sortTransparent 1\\n    -controllers 1\\n    -nurbsCurves 1\\n    -nurbsSurfaces 1\\n    -polymeshes 1\\n    -subdivSurfaces 1\\n    -planes 1\\n    -lights 1\\n    -cameras 1\\n    -controlVertices 1\\n    -hulls 1\\n    -grid 1\\n    -imagePlane 1\\n    -joints 1\\n    -ikHandles 1\\n    -deformers 1\\n    -dynamics 1\\n    -particleInstancers 1\\n    -fluids 1\\n    -hairSystems 1\\n    -follicles 1\\n    -nCloths 1\\n    -nParticles 1\\n    -nRigids 1\\n    -dynamicConstraints 1\\n    -locators 1\\n    -manipulators 1\\n    -pluginShapes 1\\n    -dimensions 1\\n    -handles 1\\n    -pivots 1\\n    -textures 1\\n    -strokes 1\\n    -motionTrails 1\\n    -clipGhosts 1\\n    -greasePencils 1\\n    -shadows 0\\n    -captureSequenceNumber -1\\n    -width 1050\\n    -height 744\\n    -sceneRenderFilter 0\\n    -activeShadingGraph \\\"ballora_animatronic_shadow_rig:rsMaterial1SG,ballora_animatronic_shadow_rig:MAT_ballora,ballora_animatronic_shadow_rig:MAT_ballora\\\" \\n    -activeCustomGeometry \\\"meshShaderball\\\" \\n    $editorName;\\nmodelEditor -e -viewSelected 0 $editorName;\\nmodelEditor -e \\n    -pluginObjects \\\"gpuCacheDisplayFilter\\\" 1 \\n    $editorName\"\n"
		+ "\t\t\t\t\t\"modelPanel -edit -l (localizedPanelLabel(\\\"Persp View\\\")) -mbv $menusOkayInPanels  $panelName;\\n$editorName = $panelName;\\nmodelEditor -e \\n    -docTag \\\"RADRENDER\\\" \\n    -editorChanged \\\"updateModelPanelBar\\\" \\n    -cam `findStartUpCamera persp` \\n    -useInteractiveMode 0\\n    -displayLights \\\"default\\\" \\n    -displayAppearance \\\"smoothShaded\\\" \\n    -activeOnly 0\\n    -ignorePanZoom 0\\n    -wireframeOnShaded 0\\n    -headsUpDisplay 1\\n    -holdOuts 1\\n    -selectionHiliteDisplay 1\\n    -useDefaultMaterial 0\\n    -bufferMode \\\"double\\\" \\n    -twoSidedLighting 0\\n    -backfaceCulling 0\\n    -xray 0\\n    -jointXray 0\\n    -activeComponentsXray 0\\n    -displayTextures 0\\n    -smoothWireframe 0\\n    -lineWidth 1\\n    -textureAnisotropic 0\\n    -textureHilight 1\\n    -textureSampling 2\\n    -textureDisplay \\\"modulate\\\" \\n    -textureMaxSize 16384\\n    -fogging 0\\n    -fogSource \\\"fragment\\\" \\n    -fogMode \\\"linear\\\" \\n    -fogStart 0\\n    -fogEnd 100\\n    -fogDensity 0.1\\n    -fogColor 0.5 0.5 0.5 1 \\n    -depthOfFieldPreview 1\\n    -maxConstantTransparency 1\\n    -rendererName \\\"vp2Renderer\\\" \\n    -objectFilterShowInHUD 1\\n    -isFiltered 0\\n    -colorResolution 256 256 \\n    -bumpResolution 512 512 \\n    -textureCompression 0\\n    -transparencyAlgorithm \\\"frontAndBackCull\\\" \\n    -transpInShadows 0\\n    -cullingOverride \\\"none\\\" \\n    -lowQualityLighting 0\\n    -maximumNumHardwareLights 1\\n    -occlusionCulling 0\\n    -shadingModel 0\\n    -useBaseRenderer 0\\n    -useReducedRenderer 0\\n    -smallObjectCulling 0\\n    -smallObjectThreshold -1 \\n    -interactiveDisableShadows 0\\n    -interactiveBackFaceCull 0\\n    -sortTransparent 1\\n    -controllers 1\\n    -nurbsCurves 1\\n    -nurbsSurfaces 1\\n    -polymeshes 1\\n    -subdivSurfaces 1\\n    -planes 1\\n    -lights 1\\n    -cameras 1\\n    -controlVertices 1\\n    -hulls 1\\n    -grid 1\\n    -imagePlane 1\\n    -joints 1\\n    -ikHandles 1\\n    -deformers 1\\n    -dynamics 1\\n    -particleInstancers 1\\n    -fluids 1\\n    -hairSystems 1\\n    -follicles 1\\n    -nCloths 1\\n    -nParticles 1\\n    -nRigids 1\\n    -dynamicConstraints 1\\n    -locators 1\\n    -manipulators 1\\n    -pluginShapes 1\\n    -dimensions 1\\n    -handles 1\\n    -pivots 1\\n    -textures 1\\n    -strokes 1\\n    -motionTrails 1\\n    -clipGhosts 1\\n    -greasePencils 1\\n    -shadows 0\\n    -captureSequenceNumber -1\\n    -width 1050\\n    -height 744\\n    -sceneRenderFilter 0\\n    -activeShadingGraph \\\"ballora_animatronic_shadow_rig:rsMaterial1SG,ballora_animatronic_shadow_rig:MAT_ballora,ballora_animatronic_shadow_rig:MAT_ballora\\\" \\n    -activeCustomGeometry \\\"meshShaderball\\\" \\n    $editorName;\\nmodelEditor -e -viewSelected 0 $editorName;\\nmodelEditor -e \\n    -pluginObjects \\\"gpuCacheDisplayFilter\\\" 1 \\n    $editorName\"\n"
		+ "\t\t\t\t$configName;\n\n            setNamedPanelLayout (localizedPanelLabel(\"Current Layout\"));\n        }\n\n        panelHistory -e -clear mainPanelHistory;\n        sceneUIReplacement -clear;\n\t}\n\n\ngrid -spacing 5 -size 12 -divisions 5 -displayAxes yes -displayGridLines yes -displayDivisionLines yes -displayPerspectiveLabels no -displayOrthographicLabels no -displayAxesBold yes -perspectiveLabelPosition axis -orthographicLabelPosition edge;\nviewManip -drawCompass 0 -compassAngle 0 -frontParameters \"\" -homeParameters \"\" -selectionLockParameters \"\";\n}\n");
	setAttr ".st" 3;
createNode script -n "sceneConfigurationScriptNode";
	rename -uid "8CB61330-491A-C279-F936-B4A6EE4EBE21";
	setAttr ".b" -type "string" "playbackOptions -min 1 -max 120 -ast 1 -aet 200 ";
	setAttr ".st" 6;
createNode network -n "Eyebrows";
	rename -uid "C46E66D3-483F-B02E-CC77-CAB53E5B2CFB";
	addAttr -ci true -k true -sn "name" -ln "name" -dt "string";
	addAttr -ci true -k true -sn "enable" -ln "enable" -min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "isBuild" -ln "isBuild" -min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "class" -ln "class" -dt "string";
	addAttr -ci true -k true -sn "parent" -ln "parent" -dt "string";
	addAttr -ci true -k true -sn "control_scale" -ln "control_scale" -min 0 -max 1 -at "float";
	addAttr -ci true -k true -sn "debug_mode" -ln "debug_mode" -min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "mirror_control_scale" -ln "mirror_control_scale" -min 
		0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "list_left_brow_joints" -ln "list_left_brow_joints" 
		-dt "stringArray";
	addAttr -ci true -k true -sn "list_right_brow_joints" -ln "list_right_brow_joints" 
		-dt "stringArray";
	addAttr -ci true -k true -sn "middle_joint" -ln "middle_joint" -dt "string";
	addAttr -ci true -k true -sn "left_all_mover_joint" -ln "left_all_mover_joint" -dt "string";
	addAttr -ci true -k true -sn "right_all_mover_joint" -ln "right_all_mover_joint" 
		-dt "string";
	addAttr -ci true -k true -sn "left_all_mover_pos_pivot" -ln "left_all_mover_pos_pivot" 
		-dt "string";
	addAttr -ci true -k true -sn "right_all_mover_pos_pivot" -ln "right_all_mover_pos_pivot" 
		-dt "string";
	addAttr -ci true -k true -sn "use_custom_base_control_position" -ln "use_custom_base_control_position" 
		-min 0 -max 1 -at "bool";
	setAttr -k on ".name" -type "string" "Eyebrows";
	setAttr -k on ".enable" yes;
	setAttr -k on ".class" -type "string" "EasySkeleton.rigs.FacialGlobal.Eyebrows";
	setAttr -k on ".parent" -type "string" "facial_base";
	setAttr -k on ".control_scale" 0.40000000596046448;
	setAttr -k on ".list_left_brow_joints" -type "stringArray" 3 "LFT_brow1" "LFT_brow2" "LFT_brow3"  ;
	setAttr -k on ".list_right_brow_joints" -type "stringArray" 3 "RGT_brow1" "RGT_brow2" "RGT_brow3"  ;
	setAttr -k on ".middle_joint" -type "string" "CEN_brow";
	setAttr -k on ".left_all_mover_joint" -type "string" "";
	setAttr -k on ".right_all_mover_joint" -type "string" "";
	setAttr -k on ".left_all_mover_pos_pivot" -type "string" "LFT_brow2";
	setAttr -k on ".right_all_mover_pos_pivot" -type "string" "RGT_brow2";
	setAttr -k on ".use_custom_base_control_position" yes;
createNode network -n "Mouth";
	rename -uid "CF7AD158-4FE2-AA6C-CEBA-C1943756632B";
	addAttr -ci true -k true -sn "name" -ln "name" -dt "string";
	addAttr -ci true -k true -sn "enable" -ln "enable" -min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "isBuild" -ln "isBuild" -min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "class" -ln "class" -dt "string";
	addAttr -ci true -k true -sn "parent" -ln "parent" -dt "string";
	addAttr -ci true -k true -sn "control_scale" -ln "control_scale" -min 0 -max 1 -at "float";
	addAttr -ci true -k true -sn "debug_mode" -ln "debug_mode" -min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "mirror_control_scale" -ln "mirror_control_scale" -min 
		0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "jnt_mouth_global" -ln "jnt_mouth_global" -dt "string";
	addAttr -ci true -k true -sn "list_upper_bind" -ln "list_upper_bind" -dt "stringArray";
	addAttr -ci true -k true -sn "list_lower_bind" -ln "list_lower_bind" -dt "stringArray";
	addAttr -ci true -k true -sn "jnt_jaw" -ln "jnt_jaw" -dt "string";
	addAttr -ci true -k true -sn "use_custom_main_pivot" -ln "use_custom_main_pivot" 
		-min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "list_custom_main_pivot" -ln "list_custom_main_pivot" 
		-dt "stringArray";
	addAttr -ci true -k true -sn "list_teeth_up" -ln "list_teeth_up" -dt "stringArray";
	addAttr -ci true -k true -sn "list_teeth_low" -ln "list_teeth_low" -dt "stringArray";
	addAttr -ci true -k true -sn "list_tongue_joints_chain" -ln "list_tongue_joints_chain" 
		-dt "stringArray";
	addAttr -ci true -k true -sn "enable_curve_blendshape" -ln "enable_curve_blendshape" 
		-min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "list_curve_up" -ln "list_curve_up" -dt "stringArray";
	addAttr -ci true -k true -sn "list_curve_low" -ln "list_curve_low" -dt "stringArray";
	addAttr -ci true -k true -sn "value_up" -ln "value_up" -dv 3 -at "long";
	addAttr -ci true -k true -sn "value_down" -ln "value_down" -dv -3 -at "long";
	addAttr -ci true -k true -sn "value_out" -ln "value_out" -dv 3 -at "long";
	addAttr -ci true -k true -sn "value_in" -ln "value_in" -dv -3 -at "long";
	addAttr -ci true -k true -sn "clamp_top" -ln "clamp_top" -min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "clamp_down" -ln "clamp_down" -min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "clamp_in" -ln "clamp_in" -min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "clamp_out" -ln "clamp_out" -min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "enable_mesh_blendshape" -ln "enable_mesh_blendshape" 
		-min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "list_shape_up" -ln "list_shape_up" -dt "stringArray";
	addAttr -ci true -k true -sn "list_shape_low" -ln "list_shape_low" -dt "stringArray";
	addAttr -ci true -k true -sn "list_shape_in" -ln "list_shape_in" -dt "stringArray";
	addAttr -ci true -k true -sn "list_shape_out" -ln "list_shape_out" -dt "stringArray";
	addAttr -ci true -k true -sn "shape_up_driven_value" -ln "shape_up_driven_value" 
		-dv 3 -at "long";
	addAttr -ci true -k true -sn "shape_down_driven_value" -ln "shape_down_driven_value" 
		-dv -3 -at "long";
	addAttr -ci true -k true -sn "shape_in_driven_value" -ln "shape_in_driven_value" 
		-dv -3 -at "long";
	addAttr -ci true -k true -sn "shape_out_driven_value" -ln "shape_out_driven_value" 
		-dv 3 -at "long";
	addAttr -ci true -k true -sn "list_target_shape" -ln "list_target_shape" -dt "stringArray";
	addAttr -ci true -k true -sn "exist_blendshape_mesh" -ln "exist_blendshape_mesh" 
		-dt "string";
	addAttr -ci true -k true -sn "enable_auto_push" -ln "enable_auto_push" -min 0 -max 
		1 -at "bool";
	addAttr -ci true -k true -sn "jaw_push_rotate_axis" -ln "jaw_push_rotate_axis" -dt "string";
	addAttr -ci true -k true -sn "invert_push_axis" -ln "invert_push_axis" -min 0 -max 
		1 -at "bool";
	addAttr -ci true -k true -sn "value_start_push" -ln "value_start_push" -at "long";
	addAttr -ci true -k true -sn "axis_side_push_in" -ln "axis_side_push_in" -dt "string";
	addAttr -ci true -k true -sn "side_parent_intensity" -ln "side_parent_intensity" 
		-dv 0.3 -at "float";
	addAttr -ci true -k true -sn "side_control_intensity" -ln "side_control_intensity" 
		-dv 1.5 -at "float";
	addAttr -ci true -k true -sn "enable_zipper" -ln "enable_zipper" -min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "mirror_scale_controls" -ln "mirror_scale_controls" 
		-min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "curve_up_weight_path" -ln "curve_up_weight_path" -dt "string";
	addAttr -ci true -k true -sn "curve_low_weight_path" -ln "curve_low_weight_path" 
		-dt "string";
	addAttr -ci true -k true -sn "mirror_scale_control" -ln "mirror_scale_control" -min 
		0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "enable_mesh_blend_shape" -ln "enable_mesh_blend_shape" 
		-min 0 -max 1 -at "bool";
	setAttr -k on ".name" -type "string" "Mouth";
	setAttr -k on ".enable" yes;
	setAttr -k on ".class" -type "string" "EasySkeleton.rigs.FacialGlobal.Mouth";
	setAttr -k on ".parent" -type "string" "facial_base";
	setAttr -k on ".control_scale" 0.40000000596046448;
	setAttr -k on ".mirror_control_scale" yes;
	setAttr -k on ".jnt_mouth_global" -type "string" "mouthBase";
	setAttr -k on ".list_upper_bind" -type "stringArray" 9 "RGT_lipCorner1" "RGT_lipUp3" "RGT_lipUp2" "RGT_lipUp1" "CEN_lipUp" "LFT_lipUp1" "LFT_lipUp2" "LFT_lipUp3" "LFT_lipCorner1"  ;
	setAttr -k on ".list_lower_bind" -type "stringArray" 7 "RGT_lipLow3" "RGT_lipLow2" "RGT_lipLow1" "CEN_lipLow" "LFT_lipLow1" "LFT_lipLow2" "LFT_lipLow3"  ;
	setAttr -k on ".jnt_jaw" -type "string" "jaw";
	setAttr -k on ".list_custom_main_pivot" -type "stringArray" 0  ;
	setAttr -k on ".list_teeth_up" -type "stringArray" 1 "CEN_teethUp"  ;
	setAttr -k on ".list_teeth_low" -type "stringArray" 1 "CEN_teethLow"  ;
	setAttr -k on ".list_tongue_joints_chain" -type "stringArray" 4 "tongue1" "tongue2" "tongue3" "tongue4"  ;
	setAttr -k on ".list_curve_up" -type "stringArray" 0  ;
	setAttr -k on ".list_curve_low" -type "stringArray" 0  ;
	setAttr -k on ".clamp_top" yes;
	setAttr -k on ".clamp_down" yes;
	setAttr -k on ".clamp_in" yes;
	setAttr -k on ".clamp_out" yes;
	setAttr -k on ".list_shape_up" -type "stringArray" 0  ;
	setAttr -k on ".list_shape_low" -type "stringArray" 0  ;
	setAttr -k on ".list_shape_in" -type "stringArray" 0  ;
	setAttr -k on ".list_shape_out" -type "stringArray" 0  ;
	setAttr -k on ".list_target_shape" -type "stringArray" 0  ;
	setAttr -k on ".exist_blendshape_mesh" -type "string" "";
	setAttr -k on ".enable_auto_push" yes;
	setAttr -k on ".jaw_push_rotate_axis" -type "string" "x";
	setAttr -k on ".axis_side_push_in" -type "string" "z";
	setAttr -k on ".enable_zipper" yes;
	setAttr -k on ".curve_up_weight_path" -type "string" "";
	setAttr -k on ".curve_low_weight_path" -type "string" "";
createNode network -n "GlobalEye";
	rename -uid "F8C89E6E-4B1B-F45A-2B02-C7A5590D93B1";
	addAttr -ci true -k true -sn "name" -ln "name" -dt "string";
	addAttr -ci true -k true -sn "enable" -ln "enable" -min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "isBuild" -ln "isBuild" -min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "class" -ln "class" -dt "string";
	addAttr -ci true -k true -sn "parent" -ln "parent" -dt "string";
	addAttr -ci true -k true -sn "control_scale" -ln "control_scale" -min 0 -max 1 -at "float";
	addAttr -ci true -k true -sn "debug_mode" -ln "debug_mode" -min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "mirror_control_scale" -ln "mirror_control_scale" -min 
		0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "left_eye_joint" -ln "left_eye_joint" -dt "string";
	addAttr -ci true -k true -sn "left_eye_aim_axis" -ln "left_eye_aim_axis" -dt "string";
	addAttr -ci true -k true -sn "left_eye_up_axis" -ln "left_eye_up_axis" -dt "string";
	addAttr -ci true -k true -sn "right_eye_joint" -ln "right_eye_joint" -dt "string";
	addAttr -ci true -k true -sn "right_eye_aim_axis" -ln "right_eye_aim_axis" -dt "string";
	addAttr -ci true -k true -sn "right_eye_up_axis" -ln "right_eye_up_axis" -dt "string";
	addAttr -ci true -k true -sn "left_eye_control_pivot" -ln "left_eye_control_pivot" 
		-dt "string";
	addAttr -ci true -k true -sn "right_eye_control_pivot" -ln "right_eye_control_pivot" 
		-dt "string";
	setAttr -k on ".name" -type "string" "GlobalEye";
	setAttr -k on ".enable" yes;
	setAttr -k on ".class" -type "string" "EasySkeleton.rigs.FacialGlobal.EyeGlobalAim";
	setAttr -k on ".parent" -type "string" "facial_base";
	setAttr -k on ".control_scale" 0.40000000596046448;
	setAttr -k on ".left_eye_joint" -type "string" "LFT_eyeBall";
	setAttr -k on ".left_eye_aim_axis" -type "string" "z";
	setAttr -k on ".left_eye_up_axis" -type "string" "y";
	setAttr -k on ".right_eye_joint" -type "string" "RGT_eyeBall";
	setAttr -k on ".right_eye_aim_axis" -type "string" "-z";
	setAttr -k on ".right_eye_up_axis" -type "string" "-y";
	setAttr -k on ".left_eye_control_pivot" -type "string" "LFT_eyeBallCtrlPiv";
	setAttr -k on ".right_eye_control_pivot" -type "string" "RGT_eyeBallCtrlPiv";
createNode network -n "LFT_EyeLid";
	rename -uid "896245A6-4D4F-0716-A65F-81B8F77E729E";
	addAttr -ci true -k true -sn "name" -ln "name" -dt "string";
	addAttr -ci true -k true -sn "enable" -ln "enable" -min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "isBuild" -ln "isBuild" -min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "class" -ln "class" -dt "string";
	addAttr -ci true -k true -sn "parent" -ln "parent" -dt "string";
	addAttr -ci true -k true -sn "control_scale" -ln "control_scale" -min 0 -max 1 -at "float";
	addAttr -ci true -k true -sn "debug_mode" -ln "debug_mode" -min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "mirror_control_scale" -ln "mirror_control_scale" -min 
		0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "list_main_control_pivot" -ln "list_main_control_pivot" 
		-dt "stringArray";
	addAttr -ci true -k true -sn "jnt_eye_ball" -ln "jnt_eye_ball" -dt "string";
	addAttr -ci true -k true -sn "jnt_eye_global" -ln "jnt_eye_global" -dt "string";
	addAttr -ci true -k true -sn "list_jnt_lid_upper" -ln "list_jnt_lid_upper" -dt "stringArray";
	addAttr -ci true -k true -sn "list_jnt_lid_lower" -ln "list_jnt_lid_lower" -dt "stringArray";
	addAttr -ci true -k true -sn "axis_up_eye_ball" -ln "axis_up_eye_ball" -min 0 -max 
		2 -en "X:Y:Z" -at "enum";
	addAttr -ci true -k true -sn "axis_aim_eye_ball" -ln "axis_aim_eye_ball" -min 0 
		-max 2 -en "X:Y:Z" -at "enum";
	addAttr -ci true -k true -sn "value_up_control_drive" -ln "value_up_control_drive" 
		-dv 3 -at "float";
	addAttr -ci true -k true -sn "value_down_control_drive" -ln "value_down_control_drive" 
		-dv 3 -at "float";
	addAttr -ci true -k true -sn "value_up_rotate_in" -ln "value_up_rotate_in" -dv 45 
		-at "float";
	addAttr -ci true -k true -sn "value_down_rotate_in" -ln "value_down_rotate_in" -dv 
		45 -at "float";
	addAttr -ci true -k true -sn "curve_blend_shape_up_rotate_in" -ln "curve_blend_shape_up_rotate_in" 
		-dt "string";
	addAttr -ci true -k true -sn "curve_blend_shape_up_rotate_out" -ln "curve_blend_shape_up_rotate_out" 
		-dt "string";
	addAttr -ci true -k true -sn "curve_blend_shape_up_push" -ln "curve_blend_shape_up_push" 
		-dt "string";
	addAttr -ci true -k true -sn "curve_blend_shape_down_rotate_in" -ln "curve_blend_shape_down_rotate_in" 
		-dt "string";
	addAttr -ci true -k true -sn "curve_blend_shape_down_rotate_out" -ln "curve_blend_shape_down_rotate_out" 
		-dt "string";
	addAttr -ci true -k true -sn "curve_blend_shape_low_push" -ln "curve_blend_shape_low_push" 
		-dt "string";
	addAttr -ci true -k true -sn "target_blend_shape" -ln "target_blend_shape" -dt "string";
	addAttr -ci true -k true -sn "mesh_blend_shape_up_push_volume" -ln "mesh_blend_shape_up_push_volume" 
		-dt "string";
	addAttr -ci true -k true -sn "mesh_blend_shape_up_rotate_in" -ln "mesh_blend_shape_up_rotate_in" 
		-dt "string";
	addAttr -ci true -k true -sn "mesh_blend_shape_up_rotate_out" -ln "mesh_blend_shape_up_rotate_out" 
		-dt "string";
	addAttr -ci true -k true -sn "mesh_blend_shape_down_push_volume" -ln "mesh_blend_shape_down_push_volume" 
		-dt "string";
	addAttr -ci true -k true -sn "mesh_blend_shape_down_rotate_in" -ln "mesh_blend_shape_down_rotate_in" 
		-dt "string";
	addAttr -ci true -k true -sn "mesh_blend_shape_down_rotate_out" -ln "mesh_blend_shape_down_rotate_out" 
		-dt "string";
	addAttr -ci true -k true -sn "enable_auto_fleshy" -ln "enable_auto_fleshy" -min 
		0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "value_fleshy_up_intensity" -ln "value_fleshy_up_intensity" 
		-dv 0.2 -at "float";
	addAttr -ci true -k true -sn "value_fleshy_side_intensity" -ln "value_fleshy_side_intensity" 
		-dv 0.2 -at "float";
	addAttr -ci true -k true -sn "list_upper_outer_joint" -ln "list_upper_outer_joint" 
		-dt "stringArray";
	addAttr -ci true -k true -sn "list_lower_outer_joint" -ln "list_lower_outer_joint" 
		-dt "stringArray";
	addAttr -ci true -k true -sn "curve_up_weight_path" -ln "curve_up_weight_path" -dt "string";
	addAttr -ci true -k true -sn "curve_low_weight_path" -ln "curve_low_weight_path" 
		-dt "string";
	addAttr -ci true -k true -sn "sync_option_shape_path" -ln "sync_option_shape_path" 
		-dt "string";
	addAttr -ci true -k true -sn "preserve_corner_joint_curve" -ln "preserve_corner_joint_curve" 
		-min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "list_eye_global_constraint" -ln "list_eye_global_constraint" 
		-dt "stringArray";
	setAttr -k on ".name" -type "string" "LFT_EyeLid";
	setAttr -k on ".enable" yes;
	setAttr -k on ".class" -type "string" "EasySkeleton.rigs.FacialGlobal.EyeLidCurveBased";
	setAttr -k on ".parent" -type "string" "facial_base";
	setAttr -k on ".control_scale" 0.40000000596046448;
	setAttr -k on ".list_main_control_pivot" -type "stringArray" 4 "LFT_eyelidInnerCtrlGuide" "LFT_eyelidUpCtrlGuide" "LFT_eyelidOuterCtrlGuide" "LFT_eyelidLowCtrlGuide"  ;
	setAttr -k on ".jnt_eye_ball" -type "string" "LFT_eyeBall";
	setAttr -k on ".jnt_eye_global" -type "string" "LFT_eyeBallBase";
	setAttr -k on ".list_jnt_lid_upper" -type "stringArray" 5 "LFT_eyelidUp1" "LFT_eyelidUp2" "LFT_eyelidUp3" "LFT_eyelidUp4" "LFT_eyelidUp5"  ;
	setAttr -k on ".list_jnt_lid_lower" -type "stringArray" 3 "LFT_eyelidLow1" "LFT_eyelidLow2" "LFT_eyelidLow3"  ;
	setAttr -k on ".axis_up_eye_ball" 1;
	setAttr -k on ".axis_aim_eye_ball" 2;
	setAttr -k on ".curve_blend_shape_up_rotate_in" -type "string" "";
	setAttr -k on ".curve_blend_shape_up_rotate_out" -type "string" "";
	setAttr -k on ".curve_blend_shape_up_push" -type "string" "";
	setAttr -k on ".curve_blend_shape_down_rotate_in" -type "string" "";
	setAttr -k on ".curve_blend_shape_down_rotate_out" -type "string" "";
	setAttr -k on ".curve_blend_shape_low_push" -type "string" "";
	setAttr -k on ".target_blend_shape" -type "string" "";
	setAttr -k on ".mesh_blend_shape_up_push_volume" -type "string" "";
	setAttr -k on ".mesh_blend_shape_up_rotate_in" -type "string" "";
	setAttr -k on ".mesh_blend_shape_up_rotate_out" -type "string" "";
	setAttr -k on ".mesh_blend_shape_down_push_volume" -type "string" "";
	setAttr -k on ".mesh_blend_shape_down_rotate_in" -type "string" "";
	setAttr -k on ".mesh_blend_shape_down_rotate_out" -type "string" "";
	setAttr -k on ".enable_auto_fleshy" yes;
	setAttr -k on ".list_upper_outer_joint" -type "stringArray" 0  ;
	setAttr -k on ".list_lower_outer_joint" -type "stringArray" 0  ;
	setAttr -k on ".curve_up_weight_path" -type "string" "";
	setAttr -k on ".curve_low_weight_path" -type "string" "";
	setAttr -k on ".sync_option_shape_path" -type "string" "";
	setAttr -k on ".preserve_corner_joint_curve" yes;
	setAttr -k on ".list_eye_global_constraint" -type "stringArray" 0  ;
createNode network -n "RGT_EyeLid";
	rename -uid "EE4C4294-445C-88F5-0C59-D3ABF6A17D19";
	addAttr -ci true -k true -sn "name" -ln "name" -dt "string";
	addAttr -ci true -k true -sn "enable" -ln "enable" -min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "isBuild" -ln "isBuild" -min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "class" -ln "class" -dt "string";
	addAttr -ci true -k true -sn "parent" -ln "parent" -dt "string";
	addAttr -ci true -k true -sn "control_scale" -ln "control_scale" -min 0 -max 1 -at "float";
	addAttr -ci true -k true -sn "debug_mode" -ln "debug_mode" -min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "mirror_control_scale" -ln "mirror_control_scale" -min 
		0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "list_main_control_pivot" -ln "list_main_control_pivot" 
		-dt "stringArray";
	addAttr -ci true -k true -sn "jnt_eye_ball" -ln "jnt_eye_ball" -dt "string";
	addAttr -ci true -k true -sn "jnt_eye_global" -ln "jnt_eye_global" -dt "string";
	addAttr -ci true -k true -sn "list_jnt_lid_upper" -ln "list_jnt_lid_upper" -dt "stringArray";
	addAttr -ci true -k true -sn "list_jnt_lid_lower" -ln "list_jnt_lid_lower" -dt "stringArray";
	addAttr -ci true -k true -sn "axis_up_eye_ball" -ln "axis_up_eye_ball" -min 0 -max 
		2 -en "X:Y:Z" -at "enum";
	addAttr -ci true -k true -sn "axis_aim_eye_ball" -ln "axis_aim_eye_ball" -min 0 
		-max 2 -en "X:Y:Z" -at "enum";
	addAttr -ci true -k true -sn "value_up_control_drive" -ln "value_up_control_drive" 
		-dv 3 -at "float";
	addAttr -ci true -k true -sn "value_down_control_drive" -ln "value_down_control_drive" 
		-dv 3 -at "float";
	addAttr -ci true -k true -sn "value_up_rotate_in" -ln "value_up_rotate_in" -dv 45 
		-at "float";
	addAttr -ci true -k true -sn "value_down_rotate_in" -ln "value_down_rotate_in" -dv 
		45 -at "float";
	addAttr -ci true -k true -sn "curve_blend_shape_up_rotate_in" -ln "curve_blend_shape_up_rotate_in" 
		-dt "string";
	addAttr -ci true -k true -sn "curve_blend_shape_up_rotate_out" -ln "curve_blend_shape_up_rotate_out" 
		-dt "string";
	addAttr -ci true -k true -sn "curve_blend_shape_up_push" -ln "curve_blend_shape_up_push" 
		-dt "string";
	addAttr -ci true -k true -sn "curve_blend_shape_down_rotate_in" -ln "curve_blend_shape_down_rotate_in" 
		-dt "string";
	addAttr -ci true -k true -sn "curve_blend_shape_down_rotate_out" -ln "curve_blend_shape_down_rotate_out" 
		-dt "string";
	addAttr -ci true -k true -sn "curve_blend_shape_low_push" -ln "curve_blend_shape_low_push" 
		-dt "string";
	addAttr -ci true -k true -sn "target_blend_shape" -ln "target_blend_shape" -dt "string";
	addAttr -ci true -k true -sn "mesh_blend_shape_up_push_volume" -ln "mesh_blend_shape_up_push_volume" 
		-dt "string";
	addAttr -ci true -k true -sn "mesh_blend_shape_up_rotate_in" -ln "mesh_blend_shape_up_rotate_in" 
		-dt "string";
	addAttr -ci true -k true -sn "mesh_blend_shape_up_rotate_out" -ln "mesh_blend_shape_up_rotate_out" 
		-dt "string";
	addAttr -ci true -k true -sn "mesh_blend_shape_down_push_volume" -ln "mesh_blend_shape_down_push_volume" 
		-dt "string";
	addAttr -ci true -k true -sn "mesh_blend_shape_down_rotate_in" -ln "mesh_blend_shape_down_rotate_in" 
		-dt "string";
	addAttr -ci true -k true -sn "mesh_blend_shape_down_rotate_out" -ln "mesh_blend_shape_down_rotate_out" 
		-dt "string";
	addAttr -ci true -k true -sn "enable_auto_fleshy" -ln "enable_auto_fleshy" -min 
		0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "value_fleshy_up_intensity" -ln "value_fleshy_up_intensity" 
		-dv 0.2 -at "float";
	addAttr -ci true -k true -sn "value_fleshy_side_intensity" -ln "value_fleshy_side_intensity" 
		-dv 0.2 -at "float";
	addAttr -ci true -k true -sn "list_upper_outer_joint" -ln "list_upper_outer_joint" 
		-dt "stringArray";
	addAttr -ci true -k true -sn "list_lower_outer_joint" -ln "list_lower_outer_joint" 
		-dt "stringArray";
	addAttr -ci true -k true -sn "curve_up_weight_path" -ln "curve_up_weight_path" -dt "string";
	addAttr -ci true -k true -sn "curve_low_weight_path" -ln "curve_low_weight_path" 
		-dt "string";
	addAttr -ci true -k true -sn "sync_option_shape_path" -ln "sync_option_shape_path" 
		-dt "string";
	addAttr -ci true -k true -sn "preserve_corner_joint_curve" -ln "preserve_corner_joint_curve" 
		-min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "list_eye_global_constraint" -ln "list_eye_global_constraint" 
		-dt "stringArray";
	setAttr -k on ".name" -type "string" "RGT_EyeLid";
	setAttr -k on ".enable" yes;
	setAttr -k on ".class" -type "string" "EasySkeleton.rigs.FacialGlobal.EyeLidCurveBased";
	setAttr -k on ".parent" -type "string" "facial_base";
	setAttr -k on ".control_scale" 0.40000000596046448;
	setAttr -k on ".mirror_control_scale" yes;
	setAttr -k on ".list_main_control_pivot" -type "stringArray" 4 "RGT_eyelidInnerCtrlGuide" "RGT_eyelidUpCtrlGuide" "RGT_eyelidOuterCtrlGuide" "RGT_eyelidLowCtrlGuide"  ;
	setAttr -k on ".jnt_eye_ball" -type "string" "RGT_eyeBall";
	setAttr -k on ".jnt_eye_global" -type "string" "RGT_eyeBallBase";
	setAttr -k on ".list_jnt_lid_upper" -type "stringArray" 5 "RGT_eyelidUp1" "RGT_eyelidUp2" "RGT_eyelidUp3" "RGT_eyelidUp4" "RGT_eyelidUp5"  ;
	setAttr -k on ".list_jnt_lid_lower" -type "stringArray" 3 "RGT_eyelidLow1" "RGT_eyelidLow2" "RGT_eyelidLow3"  ;
	setAttr -k on ".axis_up_eye_ball" 1;
	setAttr -k on ".axis_aim_eye_ball" 2;
	setAttr -k on ".curve_blend_shape_up_rotate_in" -type "string" "";
	setAttr -k on ".curve_blend_shape_up_rotate_out" -type "string" "";
	setAttr -k on ".curve_blend_shape_up_push" -type "string" "";
	setAttr -k on ".curve_blend_shape_down_rotate_in" -type "string" "";
	setAttr -k on ".curve_blend_shape_down_rotate_out" -type "string" "";
	setAttr -k on ".curve_blend_shape_low_push" -type "string" "";
	setAttr -k on ".target_blend_shape" -type "string" "";
	setAttr -k on ".mesh_blend_shape_up_push_volume" -type "string" "";
	setAttr -k on ".mesh_blend_shape_up_rotate_in" -type "string" "";
	setAttr -k on ".mesh_blend_shape_up_rotate_out" -type "string" "";
	setAttr -k on ".mesh_blend_shape_down_push_volume" -type "string" "";
	setAttr -k on ".mesh_blend_shape_down_rotate_in" -type "string" "";
	setAttr -k on ".mesh_blend_shape_down_rotate_out" -type "string" "";
	setAttr -k on ".enable_auto_fleshy" yes;
	setAttr -k on ".list_upper_outer_joint" -type "stringArray" 0  ;
	setAttr -k on ".list_lower_outer_joint" -type "stringArray" 0  ;
	setAttr -k on ".curve_up_weight_path" -type "string" "";
	setAttr -k on ".curve_low_weight_path" -type "string" "";
	setAttr -k on ".sync_option_shape_path" -type "string" "";
	setAttr -k on ".preserve_corner_joint_curve" yes;
	setAttr -k on ".list_eye_global_constraint" -type "stringArray" 0  ;
createNode network -n "FacialSecondary";
	rename -uid "209F6445-4FC9-3E80-45CB-B4A14CCA053A";
	addAttr -ci true -k true -sn "name" -ln "name" -dt "string";
	addAttr -ci true -k true -sn "enable" -ln "enable" -min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "isBuild" -ln "isBuild" -min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "class" -ln "class" -dt "string";
	addAttr -ci true -k true -sn "parent" -ln "parent" -dt "string";
	addAttr -ci true -k true -sn "control_scale" -ln "control_scale" -min 0 -max 1 -at "float";
	addAttr -ci true -k true -sn "debug_mode" -ln "debug_mode" -min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "mirror_control_scale" -ln "mirror_control_scale" -min 
		0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "blend_shape_node_name" -ln "blend_shape_node_name" 
		-dt "string";
	addAttr -ci true -k true -sn "mesh_blend_shape_target" -ln "mesh_blend_shape_target" 
		-dt "string";
	addAttr -ci true -k true -sn "L_cheek_joint" -ln "L_cheek_joint" -dt "string";
	addAttr -ci true -k true -sn "L_enable_puff_blend_shape" -ln "L_enable_puff_blend_shape" 
		-min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "L_list_blend_shape" -ln "L_list_blend_shape" -dt "stringArray";
	addAttr -ci true -k true -sn "R_cheek_joint" -ln "R_cheek_joint" -dt "string";
	addAttr -ci true -k true -sn "R_enable_puff_blend_shape" -ln "R_enable_puff_blend_shape" 
		-min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "R_list_blend_shape" -ln "R_list_blend_shape" -dt "stringArray";
	addAttr -ci true -k true -sn "L_list_left_ear_chain" -ln "L_list_left_ear_chain" 
		-dt "stringArray";
	addAttr -ci true -k true -sn "R_list_left_ear_chain" -ln "R_list_left_ear_chain" 
		-dt "stringArray";
	addAttr -ci true -k true -sn "enable_nose_joint" -ln "enable_nose_joint" -min 0 
		-max 1 -at "bool";
	addAttr -ci true -k true -sn "L_nose_wing_joint" -ln "L_nose_wing_joint" -dt "string";
	addAttr -ci true -k true -sn "R_nose_wing_joint" -ln "R_nose_wing_joint" -dt "string";
	addAttr -ci true -k true -sn "nose_base_joint" -ln "nose_base_joint" -dt "string";
	addAttr -ci true -k true -sn "nose_tip_joint" -ln "nose_tip_joint" -dt "string";
	setAttr -k on ".name" -type "string" "FacialSecondary";
	setAttr -k on ".enable" yes;
	setAttr -k on ".class" -type "string" "EasySkeleton.rigs.FacialGlobal.FacialSecondaryGlobal";
	setAttr -k on ".parent" -type "string" "facial_base";
	setAttr -k on ".control_scale" 0.40000000596046448;
	setAttr -k on ".blend_shape_node_name" -type "string" "";
	setAttr -k on ".mesh_blend_shape_target" -type "string" "";
	setAttr -k on ".L_cheek_joint" -type "string" "LFT_cheek";
	setAttr -k on ".L_list_blend_shape" -type "stringArray" 0  ;
	setAttr -k on ".R_cheek_joint" -type "string" "RGT_cheek";
	setAttr -k on ".R_list_blend_shape" -type "stringArray" 0  ;
	setAttr -k on ".L_list_left_ear_chain" -type "stringArray" 2 "LFT_ear1" "LFT_ear2"  ;
	setAttr -k on ".R_list_left_ear_chain" -type "stringArray" 2 "RGT_ear1" "RGT_ear2"  ;
	setAttr -k on ".enable_nose_joint" yes;
	setAttr -k on ".L_nose_wing_joint" -type "string" "LFT_nose_wing";
	setAttr -k on ".R_nose_wing_joint" -type "string" "RGT_nose_wing";
	setAttr -k on ".nose_base_joint" -type "string" "nose_base";
	setAttr -k on ".nose_tip_joint" -type "string" "nose_tip";
select -ne :time1;
	setAttr -av -k on ".cch";
	setAttr -av -k on ".fzn";
	setAttr -av -cb on ".ihi";
	setAttr -av -k on ".nds";
	setAttr -cb on ".bnm";
	setAttr -k on ".o" 1;
	setAttr -av -k on ".unw" 1;
	setAttr -av -k on ".etw";
	setAttr -av -k on ".tps";
	setAttr -av -k on ".tms";
select -ne :hardwareRenderingGlobals;
	setAttr -av -k on ".cch";
	setAttr -av -k on ".fzn";
	setAttr -av -k on ".ihi";
	setAttr -av -k on ".nds";
	setAttr -cb on ".bnm";
	setAttr -av -k on ".rm";
	setAttr -av -k on ".lm";
	setAttr ".otfna" -type "stringArray" 22 "NURBS Curves" "NURBS Surfaces" "Polygons" "Subdiv Surface" "Particles" "Particle Instance" "Fluids" "Strokes" "Image Planes" "UI" "Lights" "Cameras" "Locators" "Joints" "IK Handles" "Deformers" "Motion Trails" "Components" "Hair Systems" "Follicles" "Misc. UI" "Ornaments"  ;
	setAttr ".otfva" -type "Int32Array" 22 0 1 1 1 1 1
		 1 1 1 0 0 0 0 0 0 0 0 0
		 0 0 0 0 ;
	setAttr -av -k on ".hom";
	setAttr -av -k on ".hodm";
	setAttr -av -k on ".xry";
	setAttr -av -k on ".jxr";
	setAttr -av -k on ".sslt";
	setAttr -av -k on ".cbr";
	setAttr -av -k on ".bbr";
	setAttr -av -k on ".mhl";
	setAttr -k on ".cons";
	setAttr -k on ".vac";
	setAttr -av -k on ".hwi";
	setAttr -k on ".csvd";
	setAttr -av -k on ".ta";
	setAttr -av -k on ".tq";
	setAttr -k on ".ts";
	setAttr -av -k on ".etmr";
	setAttr -av -k on ".tmr";
	setAttr -av -k on ".aoon";
	setAttr -av -k on ".aoam";
	setAttr -av -k on ".aora";
	setAttr -k on ".aofr";
	setAttr -av -k on ".aosm";
	setAttr -av -k on ".hff";
	setAttr -av -k on ".hfd";
	setAttr -av -k on ".hfs";
	setAttr -av -k on ".hfe";
	setAttr -av ".hfc";
	setAttr -av -k on ".hfcr";
	setAttr -av -k on ".hfcg";
	setAttr -av -k on ".hfcb";
	setAttr -av -k on ".hfa";
	setAttr -av -k on ".mbe";
	setAttr -av -k on ".mbt";
	setAttr -av -k on ".mbsof";
	setAttr -k on ".mbsc";
	setAttr -k on ".mbc";
	setAttr -k on ".mbfa";
	setAttr -k on ".mbftb";
	setAttr -k on ".mbftg";
	setAttr -k on ".mbftr";
	setAttr -av -k on ".mbfta";
	setAttr -k on ".mbfe";
	setAttr -k on ".mbme";
	setAttr -av -k on ".mbcsx";
	setAttr -av -k on ".mbcsy";
	setAttr -av -k on ".mbasx";
	setAttr -av -k on ".mbasy";
	setAttr -av -k on ".blen";
	setAttr -av -k on ".blth";
	setAttr -av -k on ".blfr";
	setAttr -av -k on ".blfa";
	setAttr -av -k on ".blat";
	setAttr -av -k on ".msaa";
	setAttr -av -k on ".aasc";
	setAttr -av -k on ".aasq";
	setAttr -k on ".laa";
	setAttr -k on ".fprt" yes;
	setAttr -k on ".rtfm";
select -ne :renderPartition;
	setAttr -av -k on ".cch";
	setAttr -cb on ".ihi";
	setAttr -av -k on ".nds";
	setAttr -cb on ".bnm";
	setAttr -s 2 ".st";
	setAttr -cb on ".an";
	setAttr -cb on ".pt";
select -ne :renderGlobalsList1;
	setAttr -k on ".cch";
	setAttr -cb on ".ihi";
	setAttr -k on ".nds";
	setAttr -cb on ".bnm";
select -ne :defaultShaderList1;
	setAttr -k on ".cch";
	setAttr -cb on ".ihi";
	setAttr -k on ".nds";
	setAttr -cb on ".bnm";
	setAttr -s 5 ".s";
select -ne :postProcessList1;
	setAttr -k on ".cch";
	setAttr -cb on ".ihi";
	setAttr -k on ".nds";
	setAttr -cb on ".bnm";
	setAttr -s 2 ".p";
select -ne :defaultRenderingList1;
	setAttr -av -k on ".cch";
	setAttr -k on ".ihi";
	setAttr -av -k on ".nds";
	setAttr -cb on ".bnm";
select -ne :initialShadingGroup;
	setAttr -av -k on ".cch";
	setAttr -k on ".fzn";
	setAttr -cb on ".ihi";
	setAttr -av -k on ".nds";
	setAttr -cb on ".bnm";
	setAttr -k on ".bbx";
	setAttr -k on ".vwm";
	setAttr -k on ".tpv";
	setAttr -k on ".uit";
	setAttr -k on ".mwc";
	setAttr -av -cb on ".an";
	setAttr -cb on ".il";
	setAttr -cb on ".vo";
	setAttr -cb on ".eo";
	setAttr -cb on ".fo";
	setAttr -cb on ".epo";
	setAttr -k on ".ro" yes;
	setAttr -cb on ".ai_override";
	setAttr -cb on ".ai_surface_shader";
	setAttr -cb on ".ai_surface_shaderr";
	setAttr -cb on ".ai_surface_shaderg";
	setAttr -cb on ".ai_surface_shaderb";
	setAttr -cb on ".ai_volume_shader";
	setAttr -cb on ".ai_volume_shaderr";
	setAttr -cb on ".ai_volume_shaderg";
	setAttr -cb on ".ai_volume_shaderb";
select -ne :initialParticleSE;
	setAttr -av -k on ".cch";
	setAttr -k on ".fzn";
	setAttr -cb on ".ihi";
	setAttr -av -k on ".nds";
	setAttr -cb on ".bnm";
	setAttr -k on ".bbx";
	setAttr -k on ".vwm";
	setAttr -k on ".tpv";
	setAttr -k on ".uit";
	setAttr -k on ".mwc";
	setAttr -av -cb on ".an";
	setAttr -cb on ".il";
	setAttr -cb on ".vo";
	setAttr -cb on ".eo";
	setAttr -cb on ".fo";
	setAttr -cb on ".epo";
	setAttr -k on ".ro" yes;
	setAttr -cb on ".ai_override";
	setAttr -cb on ".ai_surface_shader";
	setAttr -cb on ".ai_surface_shaderr";
	setAttr -cb on ".ai_surface_shaderg";
	setAttr -cb on ".ai_surface_shaderb";
	setAttr -cb on ".ai_volume_shader";
	setAttr -cb on ".ai_volume_shaderr";
	setAttr -cb on ".ai_volume_shaderg";
	setAttr -cb on ".ai_volume_shaderb";
select -ne :defaultRenderGlobals;
	addAttr -ci true -h true -sn "dss" -ln "defaultSurfaceShader" -dt "string";
	setAttr -av -k on ".cch";
	setAttr -cb on ".ihi";
	setAttr -av -k on ".nds";
	setAttr -cb on ".bnm";
	setAttr -av -k on ".macc";
	setAttr -av -k on ".macd";
	setAttr -av -k on ".macq";
	setAttr -av -k on ".mcfr";
	setAttr -cb on ".ifg";
	setAttr -av -k on ".clip";
	setAttr -av -k on ".edm";
	setAttr -av -k on ".edl";
	setAttr -av -cb on ".ren" -type "string" "arnold";
	setAttr -av -k on ".esr";
	setAttr -av -k on ".ors";
	setAttr -cb on ".sdf";
	setAttr -av -k on ".outf";
	setAttr -av -cb on ".imfkey";
	setAttr -av -k on ".gama";
	setAttr -av -k on ".exrc";
	setAttr -av -k on ".expt";
	setAttr -av -k on ".an";
	setAttr -cb on ".ar";
	setAttr -av -k on ".fs";
	setAttr -av -k on ".ef";
	setAttr -av -k on ".bfs";
	setAttr -av -cb on ".me";
	setAttr -cb on ".se";
	setAttr -av -k on ".be";
	setAttr -av -cb on ".ep";
	setAttr -av -k on ".fec";
	setAttr -av -k on ".ofc";
	setAttr -cb on ".ofe";
	setAttr -cb on ".efe";
	setAttr -cb on ".oft";
	setAttr -cb on ".umfn";
	setAttr -cb on ".ufe";
	setAttr -av -cb on ".pff";
	setAttr -av -cb on ".peie";
	setAttr -av -cb on ".ifp";
	setAttr -k on ".rv";
	setAttr -av -k on ".comp";
	setAttr -av -k on ".cth";
	setAttr -av -k on ".soll";
	setAttr -av -k on ".sosl";
	setAttr -av -k on ".rd";
	setAttr -av -k on ".lp";
	setAttr -av -k on ".sp";
	setAttr -av -k on ".shs";
	setAttr -av -k on ".lpr";
	setAttr -cb on ".gv";
	setAttr -cb on ".sv";
	setAttr -av -k on ".mm";
	setAttr -av -k on ".npu";
	setAttr -av -k on ".itf";
	setAttr -av -k on ".shp";
	setAttr -cb on ".isp";
	setAttr -av -k on ".uf";
	setAttr -av -k on ".oi";
	setAttr -av -k on ".rut";
	setAttr -av -k on ".mot";
	setAttr -av -cb on ".mb";
	setAttr -av -k on ".mbf";
	setAttr -av -k on ".mbso";
	setAttr -av -k on ".mbsc";
	setAttr -av -k on ".afp";
	setAttr -av -k on ".pfb";
	setAttr -av -k on ".pram";
	setAttr -av -k on ".poam";
	setAttr -av -k on ".prlm";
	setAttr -av -k on ".polm";
	setAttr -av -cb on ".prm";
	setAttr -av -cb on ".pom";
	setAttr -cb on ".pfrm";
	setAttr -cb on ".pfom";
	setAttr -av -k on ".bll";
	setAttr -av -k on ".bls";
	setAttr -av -k on ".smv";
	setAttr -av -k on ".ubc";
	setAttr -av -k on ".mbc";
	setAttr -cb on ".mbt";
	setAttr -av -k on ".udbx";
	setAttr -av -k on ".smc";
	setAttr -av -k on ".kmv";
	setAttr -cb on ".isl";
	setAttr -cb on ".ism";
	setAttr -cb on ".imb";
	setAttr -av -k on ".rlen";
	setAttr -av -k on ".frts";
	setAttr -av -k on ".tlwd";
	setAttr -av -k on ".tlht";
	setAttr -av -k on ".jfc";
	setAttr -cb on ".rsb";
	setAttr -av -k on ".ope";
	setAttr -av -k on ".oppf";
	setAttr -av -k on ".rcp";
	setAttr -av -k on ".icp";
	setAttr -av -k on ".ocp";
	setAttr -cb on ".hbl";
	setAttr ".dss" -type "string" "lambert1";
select -ne :defaultResolution;
	setAttr -av -k on ".cch";
	setAttr -av -k on ".ihi";
	setAttr -av -k on ".nds";
	setAttr -k on ".bnm";
	setAttr -av -k on ".w";
	setAttr -av -k on ".h";
	setAttr -av -k on ".pa" 1;
	setAttr -av -k on ".al";
	setAttr -av -k on ".dar";
	setAttr -av -k on ".ldar";
	setAttr -av -k on ".dpi";
	setAttr -av -k on ".off";
	setAttr -av -k on ".fld";
	setAttr -av -k on ".zsl";
	setAttr -av -k on ".isu";
	setAttr -av -k on ".pdu";
select -ne :defaultColorMgtGlobals;
	setAttr ".cfe" yes;
	setAttr ".cfp" -type "string" "<MAYA_RESOURCES>/OCIO-configs/Maya2022-default/config.ocio";
	setAttr ".vtn" -type "string" "ACES 1.0 SDR-video (sRGB)";
	setAttr ".vn" -type "string" "ACES 1.0 SDR-video";
	setAttr ".dn" -type "string" "sRGB";
	setAttr ".wsn" -type "string" "ACEScg";
	setAttr ".otn" -type "string" "ACES 1.0 SDR-video (sRGB)";
	setAttr ".potn" -type "string" "ACES 1.0 SDR-video (sRGB)";
select -ne :hardwareRenderGlobals;
	setAttr -av -k on ".cch";
	setAttr -av -cb on ".ihi";
	setAttr -av -k on ".nds";
	setAttr -cb on ".bnm";
	setAttr -av -k off -cb on ".ctrs" 256;
	setAttr -av -k off -cb on ".btrs" 512;
	setAttr -av -k off -cb on ".fbfm";
	setAttr -av -k off -cb on ".ehql";
	setAttr -av -k off -cb on ".eams";
	setAttr -av -k off -cb on ".eeaa";
	setAttr -av -k off -cb on ".engm";
	setAttr -av -k off -cb on ".mes";
	setAttr -av -k off -cb on ".emb";
	setAttr -av -k off -cb on ".mbbf";
	setAttr -av -k off -cb on ".mbs";
	setAttr -av -k off -cb on ".trm";
	setAttr -av -k off -cb on ".tshc";
	setAttr -av -k off -cb on ".enpt";
	setAttr -av -k off -cb on ".clmt";
	setAttr -av -k off -cb on ".tcov";
	setAttr -av -k off -cb on ".lith";
	setAttr -av -k off -cb on ".sobc";
	setAttr -av -k off -cb on ".cuth";
	setAttr -av -k off -cb on ".hgcd";
	setAttr -av -k off -cb on ".hgci";
	setAttr -av -k off -cb on ".mgcs";
	setAttr -av -k off -cb on ".twa";
	setAttr -av -k off -cb on ".twz";
	setAttr -av -cb on ".hwcc";
	setAttr -av -cb on ".hwdp";
	setAttr -av -cb on ".hwql";
	setAttr -av -k on ".hwfr";
	setAttr -av -k on ".soll";
	setAttr -av -k on ".sosl";
	setAttr -av -k on ".bswa";
	setAttr -av -k on ".shml";
	setAttr -av -k on ".hwel";
connectAttr "rootLoc.wm" "GlobalJoints.opm";
connectAttr "GlobalJoints.s" "facial_base.is";
connectAttr "facial_base.s" "LFT_brow1.is";
connectAttr "facial_base.s" "LFT_brow2.is";
connectAttr "facial_base.s" "LFT_brow3.is";
connectAttr "facial_base.s" "CEN_brow.is";
connectAttr "facial_base.s" "jaw.is";
connectAttr "jaw.s" "mouthBase.is";
connectAttr "mouthBase.s" "RGT_lipUp3.is";
connectAttr "mouthBase.s" "RGT_lipUp2.is";
connectAttr "mouthBase.s" "RGT_lipLow1.is";
connectAttr "mouthBase.s" "RGT_lipUp1.is";
connectAttr "mouthBase.s" "RGT_lipLow2.is";
connectAttr "mouthBase.s" "RGT_lipCorner1.is";
connectAttr "mouthBase.s" "RGT_lipLow3.is";
connectAttr "mouthBase.s" "CEN_lipUp.is";
connectAttr "mouthBase.s" "LFT_lipLow3.is";
connectAttr "mouthBase.s" "LFT_lipLow1.is";
connectAttr "mouthBase.s" "LFT_lipUp3.is";
connectAttr "mouthBase.s" "LFT_lipUp2.is";
connectAttr "mouthBase.s" "LFT_lipCorner1.is";
connectAttr "mouthBase.s" "LFT_lipLow2.is";
connectAttr "mouthBase.s" "LFT_lipUp1.is";
connectAttr "mouthBase.s" "CEN_lipLow.is";
connectAttr "mouthBase.s" "CEN_teethUp.is";
connectAttr "mouthBase.s" "CEN_teethLow.is";
connectAttr "jaw.s" "tongue1.is";
connectAttr "tongue1.s" "tongue2.is";
connectAttr "tongue2.s" "tongue3.is";
connectAttr "tongue3.s" "tongue4.is";
connectAttr "facial_base.s" "RGT_brow1.is";
connectAttr "facial_base.s" "RGT_brow2.is";
connectAttr "facial_base.s" "RGT_brow3.is";
connectAttr "facial_base.s" "LFT_eyeBall.is";
connectAttr "LFT_eyeBall.s" "LFT_eyeBallCtrlPiv.is";
connectAttr "facial_base.s" "RGT_eyeBall.is";
connectAttr "RGT_eyeBall.s" "RGT_eyeBallCtrlPiv.is";
connectAttr "facial_base.s" "LFT_cheek.is";
connectAttr "facial_base.s" "RGT_cheek.is";
connectAttr "facial_base.s" "LFT_eyeBallBase.is";
connectAttr "LFT_eyeBallBase.s" "LFT_eyelidOuterCtrlGuide.is";
connectAttr "LFT_eyeBallBase.s" "LFT_eyelidInnerCtrlGuide.is";
connectAttr "LFT_eyeBallBase.s" "LFT_eyelidLowCtrlGuide.is";
connectAttr "LFT_eyeBallBase.s" "LFT_eyelidUpCtrlGuide.is";
connectAttr "LFT_eyeBallBase.s" "LFT_eyelidUp1.is";
connectAttr "LFT_eyeBallBase.s" "LFT_eyelidUp3.is";
connectAttr "LFT_eyeBallBase.s" "LFT_eyelidUp2.is";
connectAttr "LFT_eyeBallBase.s" "LFT_eyelidUp5.is";
connectAttr "LFT_eyeBallBase.s" "LFT_eyelidLow1.is";
connectAttr "LFT_eyeBallBase.s" "LFT_eyelidLow2.is";
connectAttr "LFT_eyeBallBase.s" "LFT_eyelidLow3.is";
connectAttr "LFT_eyeBallBase.s" "LFT_eyelidUp4.is";
connectAttr "facial_base.s" "RGT_eyeBallBase.is";
connectAttr "RGT_eyeBallBase.s" "RGT_eyelidOuterCtrlGuide.is";
connectAttr "RGT_eyeBallBase.s" "RGT_eyelidInnerCtrlGuide.is";
connectAttr "RGT_eyeBallBase.s" "RGT_eyelidLowCtrlGuide.is";
connectAttr "RGT_eyeBallBase.s" "RGT_eyelidUpCtrlGuide.is";
connectAttr "RGT_eyeBallBase.s" "RGT_eyelidUp1.is";
connectAttr "RGT_eyeBallBase.s" "RGT_eyelidUp3.is";
connectAttr "RGT_eyeBallBase.s" "RGT_eyelidUp2.is";
connectAttr "RGT_eyeBallBase.s" "RGT_eyelidUp5.is";
connectAttr "RGT_eyeBallBase.s" "RGT_eyelidLow1.is";
connectAttr "RGT_eyeBallBase.s" "RGT_eyelidLow2.is";
connectAttr "RGT_eyeBallBase.s" "RGT_eyelidLow3.is";
connectAttr "RGT_eyeBallBase.s" "RGT_eyelidUp4.is";
connectAttr "facial_base.s" "nose_base.is";
connectAttr "facial_base.s" "nose_tip.is";
connectAttr "facial_base.s" "LFT_nose_wing.is";
connectAttr "facial_base.s" "RGT_nose_wing.is";
connectAttr "facial_base.s" "LFT_ear1.is";
connectAttr "LFT_ear1.s" "LFT_ear2.is";
connectAttr "facial_base.s" "RGT_ear1.is";
connectAttr "RGT_ear1.s" "RGT_ear2.is";
connectAttr "rootLoc.wm" "AutoRig.opm";
relationship "link" ":lightLinker1" ":initialShadingGroup.message" ":defaultLightSet.message";
relationship "link" ":lightLinker1" ":initialParticleSE.message" ":defaultLightSet.message";
relationship "shadowLink" ":lightLinker1" ":initialShadingGroup.message" ":defaultLightSet.message";
relationship "shadowLink" ":lightLinker1" ":initialParticleSE.message" ":defaultLightSet.message";
connectAttr "layerManager.dli[0]" "defaultLayer.id";
connectAttr "renderLayerManager.rlmi[0]" "defaultRenderLayer.rlid";
connectAttr "defaultRenderLayer.msg" ":defaultRenderingList1.r" -na;
// End of facial_global.ma
