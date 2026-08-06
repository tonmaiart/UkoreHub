//Maya ASCII 2022 scene
//Name: skeleton.ma
//Last modified: Tue, Feb 11, 2025 04:42:30 PM
//Codeset: 1252
requires maya "2022";
requires "stereoCamera" "10.0";
requires "mtoa" "5.0.0.4";
currentUnit -l centimeter -a degree -t film;
fileInfo "application" "maya";
fileInfo "product" "Maya 2022";
fileInfo "version" "2022";
fileInfo "cutIdentifier" "202405021833-753375ecb3";
fileInfo "osv" "Windows 10 Home Single Language v2009 (Build: 26100)";
fileInfo "UUID" "9C21170E-4EFD-CF58-222E-E08FDA0263DC";
createNode transform -s -n "persp";
	rename -uid "A6691032-49F7-21B3-6AEA-A1BA12821C55";
	setAttr ".v" no;
	setAttr ".t" -type "double3" -16.954085459031457 26.209358613500982 69.352712900035954 ;
	setAttr ".r" -type "double3" -11.738352729681035 -13.39999999999311 2.0434785858112568e-16 ;
createNode camera -s -n "perspShape" -p "persp";
	rename -uid "BC25C809-40A8-1A1B-38EC-94A8578B54A9";
	setAttr -k off ".v" no;
	setAttr ".fl" 34.999999999999993;
	setAttr ".coi" 72.859308671217249;
	setAttr ".imn" -type "string" "persp";
	setAttr ".den" -type "string" "persp_depth";
	setAttr ".man" -type "string" "persp_mask";
	setAttr ".tp" -type "double3" 4.1323245326781137 22.528789182108007 -2.4424906541753444e-15 ;
	setAttr ".hc" -type "string" "viewSet -p %camera";
createNode transform -s -n "top";
	rename -uid "4DBDC39B-4A1F-7579-21D7-EBB5D1F93D4F";
	setAttr ".v" no;
	setAttr ".t" -type "double3" 0 1000.1 0 ;
	setAttr ".r" -type "double3" -90 0 0 ;
createNode camera -s -n "topShape" -p "top";
	rename -uid "3BE8D28C-448A-B7E1-9789-918664BDB688";
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
	rename -uid "AA68EE49-447D-802C-6BC1-8E9A4AF38C2D";
	setAttr ".v" no;
	setAttr ".t" -type "double3" 0 0 1000.1 ;
createNode camera -s -n "frontShape" -p "front";
	rename -uid "DCD46789-4866-8009-A469-F0AE8227E5B8";
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
	rename -uid "15BA9887-476E-9112-57F0-BAA65F678261";
	setAttr ".v" no;
	setAttr ".t" -type "double3" 1000.1 0 0 ;
	setAttr ".r" -type "double3" 0 90 0 ;
createNode camera -s -n "sideShape" -p "side";
	rename -uid "D5753D8F-431D-D0B6-2E57-ABA62648B58F";
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
	rename -uid "E0D4F7DB-4B07-8493-4976-169752B5505D";
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
	rename -uid "8F7D6720-40B7-79A5-1C35-1783D41CBFDB";
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
	rename -uid "A7FB6E82-486E-3C63-0C2A-EF95C1B82998";
	setAttr -l on -k off ".v";
createNode nurbsCurve -n "WorldCtrlShape" -p "WorldCtrl";
	rename -uid "841B31C5-4838-3705-C91F-20A2BA1DF8D6";
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
	rename -uid "D329D508-46AF-7DD5-4A8D-A8B9D89616CF";
	setAttr -l on -k off ".v";
createNode nurbsCurve -n "RootCtrlShape" -p "RootCtrl";
	rename -uid "FD24421B-4C7C-C15E-4AC5-759ADEF1E805";
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
	rename -uid "AAAF50E7-4057-23F8-31E8-B1A6C046D735";
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
	rename -uid "97782CC7-4789-E6E7-CC4C-4BA9BAF40F87";
	setAttr -k off ".v";
createNode transform -n "GlobalJoints" -p "CharacterRig";
	rename -uid "1ECBFA8C-4BF1-1375-2F70-CC8E5EA27BA0";
	setAttr -l on -k off ".tx";
	setAttr -l on -k off ".ty";
	setAttr -l on -k off ".tz";
	setAttr -l on -k off ".rx";
	setAttr -l on -k off ".ry";
	setAttr -l on -k off ".rz";
	setAttr -l on -k off ".sx";
	setAttr -l on -k off ".sy";
	setAttr -l on -k off ".sz";
createNode joint -n "root" -p "GlobalJoints";
	rename -uid "B1F66A65-40D7-D545-E36E-76817B9C078C";
	setAttr ".t" -type "double3" 0 14.23721611329319 0 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".radi" 0.5;
createNode joint -n "LFT_clavicle" -p "GlobalJoints";
	rename -uid "5FB72C53-4696-6F78-A325-FF93CF804553";
	setAttr ".t" -type "double3" 0.66470215329823867 22.528789182107989 -3.9873148269237655e-15 ;
	setAttr ".ro" 4;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".jo" -type "double3" 90.000000000000028 89.999999999999972 0 ;
	setAttr ".radi" 0.5;
createNode joint -n "LFT_armUp" -p "LFT_clavicle";
	rename -uid "4F3861E2-40C3-B48C-F4A3-0BA6A393CBEB";
	setAttr ".t" -type "double3" -7.8886090522101181e-31 1.4339187072871342 -1.7763568394002505e-14 ;
	setAttr ".ro" 4;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".jo" -type "double3" 4.0475528631699495e-15 1.7974745528315001e-30 -14.999999999999986 ;
	setAttr ".radi" 0.5;
createNode joint -n "LFT_armLow" -p "LFT_armUp";
	rename -uid "EF54F589-4743-1287-5405-F983D2841AC7";
	setAttr ".t" -type "double3" -1.1102230246251565e-16 3.2254770803009318 0 ;
	setAttr ".ro" 4;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".jo" -type "double3" 0 0 30.000000000000011 ;
	setAttr ".radi" 0.5;
createNode joint -n "LFT_hand" -p "LFT_armLow";
	rename -uid "0E557913-4500-2C09-D98C-C19218E3383C";
	setAttr ".t" -type "double3" -8.8817841970012523e-16 3.9285336887887992 0 ;
	setAttr ".ro" 4;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".jo" -type "double3" 0 0 -14.999999999999998 ;
	setAttr ".radi" 0.5;
createNode joint -n "LFT_palm" -p "LFT_hand";
	rename -uid "06C50CF5-4E0F-B546-4B8A-2FA65DC47F2A";
	setAttr ".t" -type "double3" 8.8817841970012523e-16 1.4328293227806679 3.5527136788005009e-15 ;
	setAttr ".ro" 4;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".jo" -type "double3" -5.0180304902484734e-45 0 0 ;
	setAttr ".radi" 0.5;
createNode joint -n "LFT_handTip" -p "LFT_palm";
	rename -uid "6E014406-4CE4-E04A-8530-3FBC1E1D1EB8";
	setAttr ".t" -type "double3" 5.5511151231257827e-17 1.2444075452671921 0 ;
	setAttr ".ro" 4;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".jo" -type "double3" -6.7625801528739209e-45 0 0 ;
	setAttr ".radi" 0.5;
createNode joint -n "LFT_index1" -p "LFT_hand";
	rename -uid "52F0EB34-41CC-B460-CEBF-F488792EC2EE";
	setAttr ".t" -type "double3" -0.58579773923892708 0.5236775746083655 0 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".jo" -type "double3" -5.0180304902484734e-45 0 0 ;
	setAttr ".ds" 1;
	setAttr ".radi" 0.5;
createNode joint -n "LFT_index2" -p "LFT_index1";
	rename -uid "895A258F-4D05-1670-C715-0C890D636ED7";
	setAttr ".t" -type "double3" -6.6613381477509392e-16 0.90915143480950356 0 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".jo" -type "double3" -5.0180304902484734e-45 0 0 ;
	setAttr ".radi" 0.5;
createNode joint -n "LFT_index3" -p "LFT_index2";
	rename -uid "E7F3D8CE-4438-E379-EFD8-50B14148BEE0";
	setAttr ".t" -type "double3" 5.5511151231257827e-16 0.42814960894081544 0 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".jo" -type "double3" 14.999999999999998 0 0 ;
	setAttr ".radi" 0.5;
createNode joint -n "LFT_index4" -p "LFT_index3";
	rename -uid "E8830CC7-4452-01C4-4497-9BAE139AB8CC";
	setAttr ".t" -type "double3" 1.1102230246251565e-16 0.43946927203362485 -1.7763568394002505e-14 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".jo" -type "double3" -5.0180304902484734e-45 0 0 ;
	setAttr ".radi" 0.5;
createNode joint -n "LFT_index5" -p "LFT_index4";
	rename -uid "5608E7F4-4E8B-C8AB-FD1D-4197D64B92E0";
	setAttr ".t" -type "double3" 7.7715611723760958e-16 0.22256462271062816 2.1316282072803006e-14 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".jo" -type "double3" -5.0180304902484734e-45 0 0 ;
	setAttr ".radi" 0.5;
createNode joint -n "LFT_middle1" -p "LFT_hand";
	rename -uid "05719966-479D-94BC-8843-49820B9AFF29";
	setAttr ".t" -type "double3" -0.26170173191106416 0.5236775746083655 3.5527136788005009e-15 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".jo" -type "double3" -5.0180304902484734e-45 0 0 ;
	setAttr ".ds" 1;
	setAttr ".radi" 0.5;
createNode joint -n "LFT_middle2" -p "LFT_middle1";
	rename -uid "FFB692C2-49C9-F1C1-FB0A-B78AD4432D76";
	setAttr ".t" -type "double3" -6.6613381477509392e-16 0.90915143480950356 0 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".radi" 0.5;
createNode joint -n "LFT_middle3" -p "LFT_middle2";
	rename -uid "887FB693-4D64-3139-6286-7A9EDD360E08";
	setAttr ".t" -type "double3" 6.6613381477509392e-16 0.42814960894081722 0 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".jo" -type "double3" 14.999999999999998 0 0 ;
	setAttr ".radi" 0.5;
createNode joint -n "LFT_middle4" -p "LFT_middle3";
	rename -uid "AF6681DF-438F-D9A1-24F0-B4893ECF0831";
	setAttr ".t" -type "double3" -2.2204460492503131e-16 0.43946927203362485 -1.0658141036401503e-14 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".radi" 0.5;
createNode joint -n "LFT_middle5" -p "LFT_middle4";
	rename -uid "DD080D52-4050-1B03-A997-98ABD4C67759";
	setAttr ".t" -type "double3" 0 0.22256462271062549 1.7763568394002505e-14 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".radi" 0.5;
createNode joint -n "LFT_pinky1" -p "LFT_hand";
	rename -uid "417B9DFD-46E1-AC2D-D34A-A6B3F9D0AD43";
	setAttr ".t" -type "double3" 0.46351028417386519 0.52367757460836906 0 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".jo" -type "double3" -5.0180304902484734e-45 0 0 ;
	setAttr ".ds" 1;
	setAttr ".radi" 0.5;
createNode joint -n "LFT_pinky2" -p "LFT_pinky1";
	rename -uid "1C9B46A9-4334-72D5-3F7A-E28D159CC85C";
	setAttr ".t" -type "double3" 0 0.9091514348095 0 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".radi" 0.5;
createNode joint -n "LFT_pinky3" -p "LFT_pinky2";
	rename -uid "AF259782-4339-7DE7-6D12-67B592AE547B";
	setAttr ".t" -type "double3" 0 0.42814960894081899 0 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".jo" -type "double3" 14.999999999999998 0 0 ;
	setAttr ".radi" 0.5;
createNode joint -n "LFT_pinky4" -p "LFT_pinky3";
	rename -uid "D99DA88B-497B-3242-9A5A-8FAFB381A8B3";
	setAttr ".t" -type "double3" -9.4368957093138306e-16 0.43946927203362396 -7.1054273576010019e-15 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".radi" 0.5;
createNode joint -n "LFT_pinky5" -p "LFT_pinky4";
	rename -uid "4FF78FA2-4ED1-783F-8468-2294AEF03328";
	setAttr ".t" -type "double3" 9.4368957093138306e-16 0.22256462271062993 1.4210854715202004e-14 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".radi" 0.5;
createNode joint -n "LFT_ring1" -p "LFT_hand";
	rename -uid "1E33BA49-4B3A-BA1F-7D80-918A4794628D";
	setAttr ".t" -type "double3" 0.1232313247895549 0.52367757460836906 3.5527136788005009e-15 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".jo" -type "double3" -5.0180304902484734e-45 0 0 ;
	setAttr ".ds" 1;
	setAttr ".radi" 0.5;
createNode joint -n "LFT_ring2" -p "LFT_ring1";
	rename -uid "85272614-4734-C127-CD89-DE8D0384235B";
	setAttr ".t" -type "double3" -4.4408920985006262e-16 0.9091514348095 0 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".radi" 0.5;
createNode joint -n "LFT_ring3" -p "LFT_ring2";
	rename -uid "EB1325D4-41D9-4C21-02EF-0C85EEC4B21C";
	setAttr ".t" -type "double3" 4.4408920985006262e-16 0.42814960894081722 0 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".jo" -type "double3" 14.999999999999998 0 0 ;
	setAttr ".radi" 0.5;
createNode joint -n "LFT_ring4" -p "LFT_ring3";
	rename -uid "D2BC97C7-4D2F-2D2A-FCFD-2197A2488C14";
	setAttr ".t" -type "double3" -4.3715031594615539e-16 0.43946927203362396 -1.4210854715202004e-14 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".radi" 0.5;
createNode joint -n "LFT_ring5" -p "LFT_ring4";
	rename -uid "4DF4F738-41F1-AE46-63D4-148FA3E6F8FF";
	setAttr ".t" -type "double3" -4.5102810375396984e-16 0.22256462271062816 2.1316282072803006e-14 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".radi" 0.5;
createNode joint -n "LFT_thumb1" -p "LFT_hand";
	rename -uid "2E857396-4305-E3FD-B909-3CB05F670DE6";
	setAttr ".t" -type "double3" -0.97396991812645639 0.52367757460836728 0 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".jo" -type "double3" -5.0180304902484734e-45 0 0 ;
	setAttr ".ds" 1;
	setAttr ".radi" 0.5;
createNode joint -n "LFT_thumb2" -p "LFT_thumb1";
	rename -uid "8814EDEE-458D-8270-9C23-56B312F416E7";
	setAttr ".t" -type "double3" 1.1102230246251565e-15 0.52049574948503796 0 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".radi" 0.5;
createNode joint -n "LFT_thumb3" -p "LFT_thumb2";
	rename -uid "B8EAEB71-4753-36E7-DA6A-079E7E9D3F1B";
	setAttr ".t" -type "double3" -6.6613381477509392e-16 0.36554180751073773 0 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".jo" -type "double3" 14.999999999999998 0 0 ;
	setAttr ".radi" 0.5;
createNode joint -n "LFT_thumb4" -p "LFT_thumb3";
	rename -uid "9911C649-4947-F738-BB69-E08CFDA9F9C0";
	setAttr ".t" -type "double3" 0 0.31399769357614105 -1.7763568394002505e-14 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".radi" 0.5;
createNode joint -n "LFT_legUp" -p "GlobalJoints";
	rename -uid "06D1AAB2-42B5-642A-E2A9-B09A0E468A15";
	setAttr ".t" -type "double3" 1.7578417703442386 14.23721611329319 0 ;
	setAttr ".ro" 4;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".jo" -type "double3" 165 0 0 ;
	setAttr ".radi" 0.5;
createNode joint -n "LFT_legLow" -p "LFT_legUp";
	rename -uid "EC4FDB0D-4086-0A9B-8652-9C9EF824D9DF";
	setAttr ".t" -type "double3" 0 4.7638597402807523 1.7763568394002505e-15 ;
	setAttr ".ro" 4;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".jo" -type "double3" 30.000000000000011 0 0 ;
	setAttr ".radi" 0.5;
createNode joint -n "LFT_ankle" -p "LFT_legLow";
	rename -uid "140F7B9F-4F89-837F-4303-78B20E55843C";
	setAttr ".t" -type "double3" 2.2204460492503131e-16 6.6639278881894413 1.5543122344752192e-15 ;
	setAttr ".ro" 4;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".jo" -type "double3" -14.999999999999998 0 0 ;
	setAttr ".radi" 0.5;
createNode joint -n "LFT_ball" -p "LFT_ankle";
	rename -uid "9CF00B07-48C0-C84F-40DD-279098C92A0D";
	setAttr ".t" -type "double3" -2.2204460492503131e-16 1.6176076322488746 -1.6157550474459961 ;
	setAttr ".ro" 4;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".jo" -type "double3" -90.000000000000028 0 0 ;
	setAttr ".ds" 3;
	setAttr ".radi" 0.5;
createNode joint -n "LFT_toe" -p "LFT_ball";
	rename -uid "FBE07832-4762-7E3D-E8B1-4CA542E398AB";
	setAttr ".t" -type "double3" 0 1.7043556115752252 -8.8817841970012523e-16 ;
	setAttr ".ro" 4;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".radi" 0.5;
createNode joint -n "LFT_endFootPiv" -p "LFT_ball";
	rename -uid "FE0D1549-48C6-6AE8-3816-12BD49D2472C";
	setAttr ".ove" yes;
	setAttr ".ovc" 16;
	setAttr ".t" -type "double3" 5.5140990884439134e-08 3.0091289306325582 1.1918208525741232 ;
	setAttr ".ro" 4;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".radi" 0.5;
createNode joint -n "LFT_outerFootPiv" -p "LFT_ball";
	rename -uid "C9559FBC-445A-F4FB-3F34-BA90265366B1";
	setAttr ".t" -type "double3" 1.2507696091818858 0 1.1918208525741207 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".radi" 0.5;
createNode joint -n "LFT_innerFootPiv" -p "LFT_ball";
	rename -uid "A4EEDD6D-4597-8805-7198-979EEDC8F158";
	setAttr ".t" -type "double3" -1.0929058763466637 -4.4408920985006262e-16 1.1918208525741203 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".radi" 0.5;
createNode joint -n "LFT_heelFootPiv" -p "LFT_ball";
	rename -uid "CEEFA3A6-4AD5-D994-48FE-119F5663F257";
	setAttr ".t" -type "double3" 5.5140990662394529e-08 -1.4431935712443642 1.1918208525741212 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".radi" 0.5;
createNode joint -n "neck1" -p "GlobalJoints";
	rename -uid "EBCF1D41-459A-C66F-2661-4EAAAD4F7DE8";
	setAttr ".t" -type "double3" 0 22.618063394857529 0 ;
	setAttr ".ro" 4;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".radi" 0.5;
createNode joint -n "neck2" -p "neck1";
	rename -uid "E3E8E4B4-4D77-B555-50F7-5D8C9C578A7E";
	setAttr ".t" -type "double3" 0 0.73442453091711357 0 ;
	setAttr ".ro" 4;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".radi" 0.5;
createNode joint -n "head" -p "neck2";
	rename -uid "723677BE-4DA5-02D8-7CF7-6DA09212E4AB";
	setAttr ".t" -type "double3" 0 1.0256717958344872 0 ;
	setAttr ".ro" 4;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".radi" 0.5;
createNode joint -n "pelvis" -p "GlobalJoints";
	rename -uid "2F5E0600-4E5F-8B1D-505D-F2BEFD62AA89";
	setAttr ".t" -type "double3" 0 15.650343096591836 0 ;
	setAttr ".ro" 4;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".radi" 0.5;
createNode transform -n "loc_fk_torso1" -p "pelvis";
	rename -uid "F3DEF5D3-4C15-24E2-CE23-C691F5F0F0E1";
	setAttr ".t" -type "double3" 0 -1.5530765651305956e-07 0 ;
createNode locator -n "loc_fk_torso1Shape" -p "loc_fk_torso1";
	rename -uid "5BAD0979-4D72-18D8-42FB-0F97A45E6D69";
	setAttr -k off ".v";
createNode joint -n "spine1" -p "GlobalJoints";
	rename -uid "D4505DB2-4F02-0885-3D60-B2BFB3279746";
	setAttr ".t" -type "double3" 0 16.05574705424964 0 ;
	setAttr ".ro" 4;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".radi" 0.5;
createNode joint -n "spine2" -p "spine1";
	rename -uid "AE1B991D-417E-34CD-D019-E18F727415ED";
	setAttr ".t" -type "double3" 0 1.6047166683938165 0 ;
	setAttr ".ro" 4;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".radi" 0.5;
createNode joint -n "spine3" -p "spine2";
	rename -uid "4BF5F93C-48A0-BCD6-3902-11B238726782";
	setAttr ".t" -type "double3" 0 1.4783108975313937 0 ;
	setAttr ".ro" 4;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".radi" 0.5;
createNode joint -n "spine4" -p "spine3";
	rename -uid "E2F09CFC-4ADA-3796-9658-628CDAF9EFBA";
	setAttr ".t" -type "double3" 0 1.3540811843834248 0 ;
	setAttr ".ro" 4;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".radi" 0.5;
createNode transform -n "loc_ik_torso" -p "spine4";
	rename -uid "D48EE762-4BDA-71AE-DCA2-3DB77E09EC35";
	setAttr ".t" -type "double3" 0 -7.3253679033769004e-07 0 ;
createNode locator -n "loc_ik_torsoShape" -p "loc_ik_torso";
	rename -uid "67962C4C-4D1A-F66A-8C39-0181626C77D1";
	setAttr -k off ".v";
createNode transform -n "loc_fk_torso5" -p "spine4";
	rename -uid "F8C603FF-44E2-3F3D-5A70-658632822A98";
	setAttr ".t" -type "double3" 0 -7.3253679033769004e-07 0 ;
createNode locator -n "loc_fk_torso5Shape" -p "loc_fk_torso5";
	rename -uid "026DD5FF-45CB-7D06-07F4-27BE6C2841C5";
	setAttr -k off ".v";
createNode transform -n "loc_fk_torso4" -p "spine3";
	rename -uid "0AD3314F-4C9E-27C0-A57D-9393D6B3E4D9";
	setAttr ".t" -type "double3" 0 2.5165132200299922e-07 0 ;
createNode locator -n "loc_fk_torso4Shape" -p "loc_fk_torso4";
	rename -uid "1EFA44E0-48EB-28F6-7E63-CDAC6FBB1F58";
	setAttr -k off ".v";
createNode transform -n "loc_fk_torso3" -p "spine2";
	rename -uid "A4380624-416F-4730-CF1A-6BB9781A1664";
	setAttr ".t" -type "double3" 0 -3.8951357339556125e-07 0 ;
createNode locator -n "loc_fk_torso3Shape" -p "loc_fk_torso3";
	rename -uid "48032ADE-4600-C0FA-4EE1-7D8F15E5D9C2";
	setAttr -k off ".v";
createNode transform -n "loc_fk_torso2" -p "spine1";
	rename -uid "14F16C32-4E07-6E4A-7C67-8D909F7AD5DB";
	setAttr ".t" -type "double3" 0 9.3159020408961624e-07 0 ;
createNode locator -n "loc_fk_torso2Shape" -p "loc_fk_torso2";
	rename -uid "5B4B62FD-4EDE-579C-6357-5AA86EA90BC1";
	setAttr -k off ".v";
createNode joint -n "RGT_clavicle" -p "GlobalJoints";
	rename -uid "BADDF342-441A-6158-7D9B-DCAB0365372B";
	setAttr ".t" -type "double3" -0.664702 22.5288 -3.9873099999999997e-15 ;
	setAttr ".ro" 4;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".jo" -type "double3" -89.999999999999972 -89.999999999999972 0 ;
	setAttr ".radi" 0.5;
createNode joint -n "RGT_armUp" -p "RGT_clavicle";
	rename -uid "C99373DE-45CA-10A2-5946-FBB29BE977F2";
	setAttr ".t" -type "double3" -7.511609782920964e-21 -1.4339179999999998 0 ;
	setAttr ".ro" 4;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".jo" -type "double3" -5.0689441988442267e-32 3.8502453745545332e-31 -14.999999999999996 ;
	setAttr ".radi" 0.5;
createNode joint -n "RGT_armLow" -p "RGT_armUp";
	rename -uid "5C8A5974-49A9-D8FB-A406-108A5A2782B8";
	setAttr ".t" -type "double3" -5.1632344644225725e-07 -3.2254755477486934 3.5527136788005009e-15 ;
	setAttr ".ro" 4;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".jo" -type "double3" -7.961746823997962e-32 -2.9713643664160548e-31 29.999999999999993 ;
	setAttr ".radi" 0.5;
createNode joint -n "RGT_hand" -p "RGT_armLow";
	rename -uid "73792DFE-4FEE-14FE-8D6C-348B115F1E5E";
	setAttr ".t" -type "double3" 2.2984918901514106e-07 -3.9285315251046349 -7.1054273576010019e-15 ;
	setAttr ".ro" 4;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".jo" -type "double3" 8.5377364625159366e-07 9.4787915988669299e-23 -14.999999999999996 ;
	setAttr ".radi" 0.5;
createNode joint -n "RGT_palm" -p "RGT_hand";
	rename -uid "6395FDC6-42CB-C62B-0B49-4DAB890DADE0";
	setAttr ".t" -type "double3" -1.3045120539345589e-15 -1.4328400000000006 3.5527136788005009e-15 ;
	setAttr ".ro" 4;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".radi" 0.5;
createNode joint -n "RGT_handTip" -p "RGT_palm";
	rename -uid "7A568458-40B9-C71C-D132-3EAC88B71E47";
	setAttr ".t" -type "double3" -6.106226635438361e-16 -1.2443999999999988 0 ;
	setAttr ".ro" 4;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".radi" 0.5;
createNode joint -n "RGT_index1" -p "RGT_hand";
	rename -uid "654AB360-4E7C-29B4-4041-7CB8AB90E395";
	setAttr ".t" -type "double3" 0.58579799999999915 -0.52367999999999881 3.5527136788005009e-15 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".ds" 1;
	setAttr ".radi" 0.5;
createNode joint -n "RGT_index2" -p "RGT_index1";
	rename -uid "F9414BF0-4786-415F-FF80-E0AA2D6F933C";
	setAttr ".t" -type "double3" -4.4408920985006262e-16 -0.90916000000000174 0 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".radi" 0.5;
createNode joint -n "RGT_index3" -p "RGT_index2";
	rename -uid "22EFE3A9-47B8-86AF-11EC-E686B4D32BB2";
	setAttr ".t" -type "double3" -2.2204460492503131e-16 -0.42809999999999881 0 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".jo" -type "double3" 15.000000000000018 2.0579703138818509e-15 2.70936931783263e-16 ;
	setAttr ".radi" 0.5;
createNode joint -n "RGT_index4" -p "RGT_index3";
	rename -uid "654A64B5-463F-EF87-495B-228177306C64";
	setAttr ".t" -type "double3" -2.2204460492503131e-16 -0.4394891205923761 -5.3674385675606118e-05 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".radi" 0.5;
createNode joint -n "RGT_index5" -p "RGT_index4";
	rename -uid "2DBE133C-47FD-1FBA-017B-F681C2110CB6";
	setAttr ".t" -type "double3" -1.1102230246251565e-16 -0.2225820296500558 8.7671027912961108e-06 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".radi" 0.5;
createNode joint -n "RGT_middle1" -p "RGT_hand";
	rename -uid "E5D46420-4508-CB54-092A-9097A1F0CCD3";
	setAttr ".t" -type "double3" 0.26170199999999916 -0.52367999999999881 3.5527136788005009e-15 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".ds" 1;
	setAttr ".radi" 0.5;
createNode joint -n "RGT_middle2" -p "RGT_middle1";
	rename -uid "A8FF0E4C-451A-3E7C-7B07-738655D3C0CB";
	setAttr ".t" -type "double3" -4.4408920985006262e-16 -0.90916000000000174 0 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".radi" 0.5;
createNode joint -n "RGT_middle3" -p "RGT_middle2";
	rename -uid "B3C2898B-45CB-1D9C-BFF5-2FA558433E2D";
	setAttr ".t" -type "double3" -2.2204460492503131e-16 -0.42809999999999881 0 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".jo" -type "double3" 15.000000000000018 2.0579703138818509e-15 2.70936931783263e-16 ;
	setAttr ".radi" 0.5;
createNode joint -n "RGT_middle4" -p "RGT_middle3";
	rename -uid "DC971CAF-4B95-C2AE-2605-0797AA9B1E5D";
	setAttr ".t" -type "double3" -2.2204460492503131e-16 -0.4394891205923761 -5.3674385675606118e-05 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".radi" 0.5;
createNode joint -n "RGT_middle5" -p "RGT_middle4";
	rename -uid "E8AD0EB1-4EE4-9145-3E8B-68A65F8000BB";
	setAttr ".t" -type "double3" -1.6653345369377348e-16 -0.2225820296500558 8.7671027912961108e-06 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".radi" 0.5;
createNode joint -n "RGT_pinky1" -p "RGT_hand";
	rename -uid "74A36CA0-4D90-B752-E092-ADB1DC201FB4";
	setAttr ".t" -type "double3" -0.46351000000000087 -0.52367999999999881 3.5527136788005009e-15 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".ds" 1;
	setAttr ".radi" 0.5;
createNode joint -n "RGT_pinky2" -p "RGT_pinky1";
	rename -uid "5D905489-4E4A-779A-6136-53BE8C6DB561";
	setAttr ".t" -type "double3" -4.4408920985006262e-16 -0.90916000000000174 0 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".radi" 0.5;
createNode joint -n "RGT_pinky3" -p "RGT_pinky2";
	rename -uid "91A6E157-4346-6A7D-34A6-EFB5F9ABE7F5";
	setAttr ".t" -type "double3" -2.2204460492503131e-16 -0.42809999999999881 0 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".jo" -type "double3" 15.000000000000018 2.0579703138818509e-15 2.70936931783263e-16 ;
	setAttr ".radi" 0.5;
createNode joint -n "RGT_pinky4" -p "RGT_pinky3";
	rename -uid "82422B46-4DEF-FE10-0344-3893B2AF7C43";
	setAttr ".t" -type "double3" -2.2204460492503131e-16 -0.4394891205923761 -5.3674385675606118e-05 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".radi" 0.5;
createNode joint -n "RGT_pinky5" -p "RGT_pinky4";
	rename -uid "EE787C44-4AF9-3A5E-E881-6C9D9C572EDB";
	setAttr ".t" -type "double3" -1.6653345369377348e-16 -0.2225820296500558 8.7671027912961108e-06 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".radi" 0.5;
createNode joint -n "RGT_ring1" -p "RGT_hand";
	rename -uid "94E76B29-448A-B8AA-CB7D-81B56E233321";
	setAttr ".t" -type "double3" -0.12323090000000084 -0.52367999999999881 3.5527136788005009e-15 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".ds" 1;
	setAttr ".radi" 0.5;
createNode joint -n "RGT_ring2" -p "RGT_ring1";
	rename -uid "01535658-43DF-FA42-3F23-919D8C7CEC24";
	setAttr ".t" -type "double3" -4.5102810375396984e-16 -0.90916000000000174 0 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".radi" 0.5;
createNode joint -n "RGT_ring3" -p "RGT_ring2";
	rename -uid "88331CAE-4063-1449-3D24-9F840F148BE1";
	setAttr ".t" -type "double3" -2.0816681711721685e-16 -0.42809999999999881 0 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".jo" -type "double3" 15.000000000000018 2.0579703138818509e-15 2.70936931783263e-16 ;
	setAttr ".radi" 0.5;
createNode joint -n "RGT_ring4" -p "RGT_ring3";
	rename -uid "AED54601-48F3-AAAF-0021-E9A714CCD73E";
	setAttr ".t" -type "double3" -2.0816681711721685e-16 -0.4394891205923761 -5.3674385675606118e-05 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".radi" 0.5;
createNode joint -n "RGT_ring5" -p "RGT_ring4";
	rename -uid "1449CA18-4820-252B-72DB-02AD9A1CB162";
	setAttr ".t" -type "double3" -1.1796119636642288e-16 -0.2225820296500558 8.7671027912961108e-06 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".radi" 0.5;
createNode joint -n "RGT_thumb1" -p "RGT_hand";
	rename -uid "5D2E6025-4120-3FB6-3CA9-9A9D618EA0A7";
	setAttr ".t" -type "double3" 0.97396599999999922 -0.52367999999999881 3.5527136788005009e-15 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".ds" 1;
	setAttr ".radi" 0.5;
createNode joint -n "RGT_thumb2" -p "RGT_thumb1";
	rename -uid "4C47A902-44F3-A959-3E6F-728ECA73EA61";
	setAttr ".t" -type "double3" -6.6613381477509392e-16 -0.5204600000000017 0 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".radi" 0.5;
createNode joint -n "RGT_thumb3" -p "RGT_thumb2";
	rename -uid "60F7D5E7-482D-8060-0DC0-B2BCCA9C8F5A";
	setAttr ".t" -type "double3" 2.2204460492503131e-16 -0.36559999999999881 0 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".jo" -type "double3" 15.000000000000018 2.0579703138818509e-15 2.70936931783263e-16 ;
	setAttr ".radi" 0.5;
createNode joint -n "RGT_thumb4" -p "RGT_thumb3";
	rename -uid "E32FB2E8-494C-9B6B-7E8F-45897F543DE2";
	setAttr ".t" -type "double3" -4.4408920985006262e-16 -0.31400729148030937 -2.9953297705276327e-05 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".radi" 0.5;
createNode joint -n "RGT_legUp" -p "GlobalJoints";
	rename -uid "5799A1CC-488E-D93D-5D5A-7CB28CB6C00E";
	setAttr ".t" -type "double3" -1.75784 14.2372 0 ;
	setAttr ".ro" 4;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".jo" -type "double3" -15.000000000000018 0 0 ;
	setAttr ".radi" 0.5;
createNode joint -n "RGT_legLow" -p "RGT_legUp";
	rename -uid "11EED441-48C7-3C63-A351-58B541404B1B";
	setAttr ".t" -type "double3" 0 -4.7638457144161794 6.2128777429393267e-06 ;
	setAttr ".ro" 4;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".jo" -type "double3" 29.999999999999986 0 0 ;
	setAttr ".radi" 0.5;
createNode joint -n "RGT_ankle" -p "RGT_legLow";
	rename -uid "A32ADC7F-4C3B-2575-003C-9FA711480ACC";
	setAttr ".t" -type "double3" 0 -6.6639284975238038 -2.4739367683324076e-06 ;
	setAttr ".ro" 4;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".jo" -type "double3" -14.99999999999997 0 0 ;
	setAttr ".radi" 0.5;
createNode joint -n "RGT_ball" -p "RGT_ankle";
	rename -uid "D44FF8F7-4BAF-E7DC-DB1E-F38084695B52";
	setAttr ".t" -type "double3" 0 -1.6176100000000022 1.6157539999999995 ;
	setAttr ".ro" 4;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".jo" -type "double3" -90.000000000000028 0 0 ;
	setAttr ".ds" 3;
	setAttr ".radi" 0.5;
createNode joint -n "RGT_toe" -p "RGT_ball";
	rename -uid "5E1DC18C-4E6F-A288-C260-1A9D00CF967B";
	setAttr ".t" -type "double3" 0 -1.70436 -6.6613381477509392e-16 ;
	setAttr ".ro" 4;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".radi" 0.5;
createNode joint -n "RGT_endFootPiv" -p "RGT_ball";
	rename -uid "237A03A3-4CF6-F271-24E5-3694FD6B8E1B";
	setAttr ".t" -type "double3" 0 -3.00913 -1.1918180000000014 ;
	setAttr ".ro" 4;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".radi" 0.5;
createNode joint -n "RGT_outerFootPiv" -p "RGT_ball";
	rename -uid "606410C4-46B0-AA2D-1861-CE9669460772";
	setAttr ".t" -type "double3" -1.25077 4.4408920985006262e-16 -1.1918179999999998 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".radi" 0.5;
createNode joint -n "RGT_innerFootPiv" -p "RGT_ball";
	rename -uid "95B66E30-4202-1EF0-A095-9B8B057E3974";
	setAttr ".t" -type "double3" 1.092904 4.4408920985006262e-16 -1.1918179999999998 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".radi" 0.5;
createNode joint -n "RGT_heelFootPiv" -p "RGT_ball";
	rename -uid "B1EBBBC5-4E30-DA4C-7FD7-C787C317368B";
	setAttr ".t" -type "double3" 0 1.4431920000000005 -1.1918179999999992 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".radi" 0.5;
createNode transform -n "LocalJoints" -p "CharacterRig";
	rename -uid "D18DA51C-4FCA-7D03-5278-3993F4D9FA42";
	setAttr -l on -k off ".tx";
	setAttr -l on -k off ".ty";
	setAttr -l on -k off ".tz";
	setAttr -l on -k off ".rx";
	setAttr -l on -k off ".ry";
	setAttr -l on -k off ".rz";
	setAttr -l on -k off ".sx";
	setAttr -l on -k off ".sy";
	setAttr -l on -k off ".sz";
createNode transform -n "AutoRig" -p "CharacterRig";
	rename -uid "F5F0808D-4017-90E5-916C-778DD1B4AE91";
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
	rename -uid "0EAE8A6F-4835-A4EE-8BD7-3BA149C8CCAA";
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
	rename -uid "5D0DA6AC-4CD2-78A8-EF6A-609CCA769B9B";
	setAttr ".v" no;
createNode transform -n "GlobalJointsBackup" -p "Others";
	rename -uid "96404EEE-4E4B-36B3-1AB2-6FB5CCCD3332";
	setAttr ".v" no;
createNode transform -n "ControllerBackup" -p "Others";
	rename -uid "90F1EA23-4A7D-B76E-094A-579F7EFC5D56";
	setAttr ".v" no;
createNode transform -n "sphere1";
	rename -uid "752596AE-47E2-BDF1-58C3-80A848E9AEF7";
createNode lightLinker -s -n "lightLinker1";
	rename -uid "D156ED3F-4D2C-49C6-3CC6-03AEF54C5CBE";
	setAttr -s 3 ".lnk";
	setAttr -s 3 ".slnk";
createNode shapeEditorManager -n "shapeEditorManager";
	rename -uid "E3EB1EE1-4F10-BCCC-A9FB-88B3451F284C";
createNode poseInterpolatorManager -n "poseInterpolatorManager";
	rename -uid "7C30A088-414B-1497-FF8D-95AB74AAAB1A";
createNode displayLayerManager -n "layerManager";
	rename -uid "5B21F3F8-4E70-F61E-45F1-41B7B9C5AA0F";
createNode displayLayer -n "defaultLayer";
	rename -uid "D0890603-4FFF-8E54-5483-6FA05E269D63";
createNode renderLayerManager -n "renderLayerManager";
	rename -uid "0678FA19-46EF-D5C5-51A1-38AF36BEB6D0";
createNode renderLayer -n "defaultRenderLayer";
	rename -uid "D9666DE8-4FDA-2A47-B630-B19B8A2FCCF3";
	setAttr ".g" yes;
createNode network -n "LFT_arm";
	rename -uid "1F84ECE9-4661-8923-3BDF-EEAE160BABD3";
	addAttr -ci true -k true -sn "name" -ln "name" -dt "string";
	addAttr -ci true -k true -sn "enable" -ln "enable" -min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "isBuild" -ln "isBuild" -min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "class" -ln "class" -dt "string";
	addAttr -ci true -k true -sn "parent" -ln "parent" -dt "string";
	addAttr -ci true -k true -sn "control_scale" -ln "control_scale" -min 0 -max 1 -at "float";
	addAttr -ci true -k true -sn "debug_mode" -ln "debug_mode" -min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "mirror_control_scale" -ln "mirror_control_scale" -min 
		0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "list_limb_joint" -ln "list_limb_joint" -dt "stringArray";
	addAttr -ci true -k true -sn "axis_forward" -ln "axis_forward" -min 0 -max 5 -en 
		"X:Y:Z:-X:-Y:-Z" -at "enum";
	addAttr -ci true -k true -sn "axis_pole" -ln "axis_pole" -min 0 -max 5 -en "X:Y:Z:-X:-Y:-Z" 
		-at "enum";
	addAttr -ci true -k true -sn "attribute_switch_range" -ln "attribute_switch_range" 
		-min 0 -max 1 -en "1:10" -at "enum";
	addAttr -ci true -k true -sn "pole_distance" -ln "pole_distance" -dv 5 -at "float";
	addAttr -ci true -k true -sn "jnt_ball" -ln "jnt_ball" -dt "string";
	addAttr -ci true -k true -sn "clavicle_enable" -ln "clavicle_enable" -min 0 -max 
		1 -at "bool";
	addAttr -ci true -k true -sn "jnt_clavicle" -ln "jnt_clavicle" -dt "string";
	addAttr -ci true -k true -sn "use_world_pole" -ln "use_world_pole" -min 0 -max 1 
		-at "bool";
	addAttr -ci true -k true -sn "world_direction_pole" -ln "world_direction_pole" -min 
		0 -max 2 -en "X:Y:Z" -at "enum";
	addAttr -ci true -k true -sn "stretch_with_fixed_angle" -ln "stretch_with_fixed_angle" 
		-min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "use_custom_fixed_angle_percentage" -ln "use_custom_fixed_angle_percentage" 
		-min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "custom_fixed_percentage" -ln "custom_fixed_percentage" 
		-at "long";
	addAttr -ci true -k true -sn "list_ik_pivot" -ln "list_ik_pivot" -dt "stringArray";
	addAttr -ci true -k true -sn "jnt_tip" -ln "jnt_tip" -dt "string";
	addAttr -ci true -k true -sn "ik_base_axis" -ln "ik_base_axis" -min 0 -max 5 -en 
		"xyz:xzy:yxz:yzx:zyx:zxy" -at "enum";
	addAttr -ci true -k true -sn "auto_roll_default_value" -ln "auto_roll_default_value" 
		-at "float";
	addAttr -ci true -k true -sn "ribbon_up_enable" -ln "ribbon_up_enable" -min 0 -max 
		1 -at "bool";
	addAttr -ci true -k true -sn "ribbon_low_enable" -ln "ribbon_low_enable" -min 0 
		-max 1 -at "bool";
	addAttr -ci true -k true -sn "list_low_ribbon_joint" -ln "list_low_ribbon_joint" 
		-dt "stringArray";
	addAttr -ci true -k true -sn "list_up_ribbon_joint" -ln "list_up_ribbon_joint" -dt "stringArray";
	addAttr -ci true -k true -sn "enable_ribbon_up_twist" -ln "enable_ribbon_up_twist" 
		-min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "enable_ribbon_low_twist" -ln "enable_ribbon_low_twist" 
		-min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "ik_pivot_enable" -ln "ik_pivot_enable" -min 0 -max 
		1 -at "bool";
	addAttr -ci true -k true -sn "invert_roll_value" -ln "invert_roll_value" -min 0 
		-max 1 -at "bool";
	addAttr -ci true -k true -sn "invert_side_roll_value" -ln "invert_side_roll_value" 
		-min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "invert_toe_twist_value" -ln "invert_toe_twist_value" 
		-min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "invert_middle_twist_value" -ln "invert_middle_twist_value" 
		-min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "invert_heel_twist_value" -ln "invert_heel_twist_value" 
		-min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "invert_roll_axis" -ln "invert_roll_axis" -min 0 -max 
		1 -at "bool";
	addAttr -ci true -k true -sn "invert_roll_side_axis" -ln "invert_roll_side_axis" 
		-min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "default_switch" -ln "default_switch" -min 0 -max 1 
		-en "FK:IK" -at "enum";
	addAttr -ci true -k true -sn "clavicle_space_switch" -ln "clavicle_space_switch" 
		-min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "list_clavicle_switch_target" -ln "list_clavicle_switch_target" 
		-dt "stringArray";
	addAttr -ci true -k true -sn "list_clavicle_switch_name" -ln "list_clavicle_switch_name" 
		-dt "stringArray";
	addAttr -ci true -k true -sn "hand_space_switch" -ln "hand_space_switch" -min 0 
		-max 1 -at "bool";
	addAttr -ci true -k true -sn "list_switch_target" -ln "list_switch_target" -dt "stringArray";
	addAttr -ci true -k true -sn "list_switch_name" -ln "list_switch_name" -dt "stringArray";
	addAttr -ci true -k true -sn "fk_space_switch" -ln "fk_space_switch" -min 0 -max 
		1 -at "bool";
	addAttr -ci true -k true -sn "list_fk_switch_target" -ln "list_fk_switch_target" 
		-dt "stringArray";
	addAttr -ci true -k true -sn "list_fk_switch_name" -ln "list_fk_switch_name" -dt "stringArray";
	addAttr -ci true -k true -sn "enable_wrist_corrective" -ln "enable_wrist_corrective" 
		-min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "list_wrist_joint" -ln "list_wrist_joint" -dt "stringArray";
	addAttr -ci true -k true -sn "wrist_corrective_axis_push" -ln "wrist_corrective_axis_push" 
		-min 0 -max 5 -en "X:Y:Z:-X:-Y:-Z" -at "enum";
	addAttr -ci true -k true -sn "wrist_axis" -ln "wrist_axis" -min 0 -max 5 -en "xyz:xzy:yxz:yzx:zyx:zxy" 
		-at "enum";
	addAttr -ci true -k true -sn "wrist_corrective_front_invert" -ln "wrist_corrective_front_invert" 
		-min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "wrist_corrective_upper_invert" -ln "wrist_corrective_upper_invert" 
		-min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "wrist_corrective_back_invert" -ln "wrist_corrective_back_invert" 
		-min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "wrist_corrective_lower_invert" -ln "wrist_corrective_lower_invert" 
		-min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "enable_elbow_corrective" -ln "enable_elbow_corrective" 
		-min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "list_elbow_joint" -ln "list_elbow_joint" -dt "stringArray";
	addAttr -ci true -k true -sn "elbow_corrective_axis_push" -ln "elbow_corrective_axis_push" 
		-min 0 -max 5 -en "X:Y:Z:-X:-Y:-Z" -at "enum";
	addAttr -ci true -k true -sn "elbow_axis" -ln "elbow_axis" -min 0 -max 5 -en "xyz:xzy:yxz:yzx:zyx:zxy" 
		-at "enum";
	addAttr -ci true -k true -sn "enable_shoulder_corrective" -ln "enable_shoulder_corrective" 
		-min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "list_shoulder_joint" -ln "list_shoulder_joint" -dt "stringArray";
	addAttr -ci true -k true -sn "shoulder_corrective_axis_push" -ln "shoulder_corrective_axis_push" 
		-min 0 -max 5 -en "X:Y:Z:-X:-Y:-Z" -at "enum";
	addAttr -ci true -k true -sn "shoulder_axis" -ln "shoulder_axis" -min 0 -max 5 -en 
		"xyz:xzy:yxz:yzx:zyx:zxy" -at "enum";
	addAttr -ci true -k true -sn "shoulder_corrective_invert" -ln "shoulder_corrective_invert" 
		-min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "auto_setup_ribbon_upper_joint" -ln "auto_setup_ribbon_upper_joint" 
		-min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "auto_setup_ribbon_lower_joint" -ln "auto_setup_ribbon_lower_joint" 
		-min 0 -max 1 -at "bool";
	setAttr -k on ".name" -type "string" "LFT_arm";
	setAttr -k on ".enable" yes;
	setAttr -k on ".class" -type "string" "EasySkeleton.rigs.BodyGlobal.Limb";
	setAttr -k on ".parent" -type "string" "spine4";
	setAttr -k on ".control_scale" 0.40000000596046448;
	setAttr -k on ".list_limb_joint" -type "stringArray" 3 "LFT_armUp" "LFT_armLow" "LFT_hand"  ;
	setAttr -k on ".axis_forward" 1;
	setAttr -k on ".pole_distance" -10;
	setAttr -k on ".jnt_ball" -type "string" "";
	setAttr -k on ".clavicle_enable" yes;
	setAttr -k on ".jnt_clavicle" -type "string" "LFT_clavicle";
	setAttr -k on ".use_world_pole" yes;
	setAttr -k on ".world_direction_pole" 2;
	setAttr -k on ".list_ik_pivot" -type "stringArray" 0  ;
	setAttr -k on ".jnt_tip" -type "string" "";
	setAttr -k on ".list_low_ribbon_joint" -type "stringArray" 0  ;
	setAttr -k on ".list_up_ribbon_joint" -type "stringArray" 0  ;
	setAttr -k on ".enable_ribbon_up_twist" yes;
	setAttr -k on ".enable_ribbon_low_twist" yes;
	setAttr -k on ".list_clavicle_switch_target" -type "stringArray" 0  ;
	setAttr -k on ".list_clavicle_switch_name" -type "stringArray" 0  ;
	setAttr -k on ".hand_space_switch" yes;
	setAttr -k on ".list_switch_target" -type "stringArray" 5 "rootLoc" "root" "pelvis" "spine4" "head"  ;
	setAttr -k on ".list_switch_name" -type "stringArray" 5 "World" "Cog" "Pelvis" "Chest" "Head"  ;
	setAttr -k on ".fk_space_switch" yes;
	setAttr -k on ".list_fk_switch_target" -type "stringArray" 4 "LFT_clavicle" "spine4" "root" "rootLoc"  ;
	setAttr -k on ".list_fk_switch_name" -type "stringArray" 4 "Clavicle" "Chest" "Cog" "World"  ;
	setAttr -k on ".list_wrist_joint" -type "stringArray" 0  ;
	setAttr -k on ".wrist_corrective_front_invert" yes;
	setAttr -k on ".wrist_corrective_upper_invert" yes;
	setAttr -k on ".list_elbow_joint" -type "stringArray" 0  ;
	setAttr -k on ".list_shoulder_joint" -type "stringArray" 0  ;
createNode network -n "LFT_leg";
	rename -uid "740E69AE-49B5-F528-48C4-B8B92D781DA4";
	addAttr -ci true -k true -sn "name" -ln "name" -dt "string";
	addAttr -ci true -k true -sn "enable" -ln "enable" -min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "isBuild" -ln "isBuild" -min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "class" -ln "class" -dt "string";
	addAttr -ci true -k true -sn "parent" -ln "parent" -dt "string";
	addAttr -ci true -k true -sn "control_scale" -ln "control_scale" -min 0 -max 1 -at "float";
	addAttr -ci true -k true -sn "debug_mode" -ln "debug_mode" -min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "mirror_control_scale" -ln "mirror_control_scale" -min 
		0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "list_limb_joint" -ln "list_limb_joint" -dt "stringArray";
	addAttr -ci true -k true -sn "axis_forward" -ln "axis_forward" -min 0 -max 5 -en 
		"X:Y:Z:-X:-Y:-Z" -at "enum";
	addAttr -ci true -k true -sn "axis_pole" -ln "axis_pole" -min 0 -max 5 -en "X:Y:Z:-X:-Y:-Z" 
		-at "enum";
	addAttr -ci true -k true -sn "attribute_switch_range" -ln "attribute_switch_range" 
		-min 0 -max 1 -en "1:10" -at "enum";
	addAttr -ci true -k true -sn "pole_distance" -ln "pole_distance" -dv 5 -at "float";
	addAttr -ci true -k true -sn "jnt_ball" -ln "jnt_ball" -dt "string";
	addAttr -ci true -k true -sn "clavicle_enable" -ln "clavicle_enable" -min 0 -max 
		1 -at "bool";
	addAttr -ci true -k true -sn "jnt_clavicle" -ln "jnt_clavicle" -dt "string";
	addAttr -ci true -k true -sn "use_world_pole" -ln "use_world_pole" -min 0 -max 1 
		-at "bool";
	addAttr -ci true -k true -sn "world_direction_pole" -ln "world_direction_pole" -min 
		0 -max 2 -en "X:Y:Z" -at "enum";
	addAttr -ci true -k true -sn "stretch_with_fixed_angle" -ln "stretch_with_fixed_angle" 
		-min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "use_custom_fixed_angle_percentage" -ln "use_custom_fixed_angle_percentage" 
		-min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "custom_fixed_percentage" -ln "custom_fixed_percentage" 
		-at "long";
	addAttr -ci true -k true -sn "list_ik_pivot" -ln "list_ik_pivot" -dt "stringArray";
	addAttr -ci true -k true -sn "jnt_tip" -ln "jnt_tip" -dt "string";
	addAttr -ci true -k true -sn "ik_base_axis" -ln "ik_base_axis" -min 0 -max 5 -en 
		"xyz:xzy:yxz:yzx:zyx:zxy" -at "enum";
	addAttr -ci true -k true -sn "auto_roll_default_value" -ln "auto_roll_default_value" 
		-at "float";
	addAttr -ci true -k true -sn "ribbon_up_enable" -ln "ribbon_up_enable" -min 0 -max 
		1 -at "bool";
	addAttr -ci true -k true -sn "ribbon_low_enable" -ln "ribbon_low_enable" -min 0 
		-max 1 -at "bool";
	addAttr -ci true -k true -sn "list_low_ribbon_joint" -ln "list_low_ribbon_joint" 
		-dt "stringArray";
	addAttr -ci true -k true -sn "list_up_ribbon_joint" -ln "list_up_ribbon_joint" -dt "stringArray";
	addAttr -ci true -k true -sn "enable_ribbon_up_twist" -ln "enable_ribbon_up_twist" 
		-min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "enable_ribbon_low_twist" -ln "enable_ribbon_low_twist" 
		-min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "ik_pivot_enable" -ln "ik_pivot_enable" -min 0 -max 
		1 -at "bool";
	addAttr -ci true -k true -sn "invert_roll_value" -ln "invert_roll_value" -min 0 
		-max 1 -at "bool";
	addAttr -ci true -k true -sn "invert_side_roll_value" -ln "invert_side_roll_value" 
		-min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "invert_toe_twist_value" -ln "invert_toe_twist_value" 
		-min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "invert_middle_twist_value" -ln "invert_middle_twist_value" 
		-min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "invert_heel_twist_value" -ln "invert_heel_twist_value" 
		-min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "invert_roll_axis" -ln "invert_roll_axis" -min 0 -max 
		1 -at "bool";
	addAttr -ci true -k true -sn "invert_roll_side_axis" -ln "invert_roll_side_axis" 
		-min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "default_switch" -ln "default_switch" -min 0 -max 1 
		-en "FK:IK" -at "enum";
	addAttr -ci true -k true -sn "clavicle_space_switch" -ln "clavicle_space_switch" 
		-min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "list_clavicle_switch_target" -ln "list_clavicle_switch_target" 
		-dt "stringArray";
	addAttr -ci true -k true -sn "list_clavicle_switch_name" -ln "list_clavicle_switch_name" 
		-dt "stringArray";
	addAttr -ci true -k true -sn "hand_space_switch" -ln "hand_space_switch" -min 0 
		-max 1 -at "bool";
	addAttr -ci true -k true -sn "list_switch_target" -ln "list_switch_target" -dt "stringArray";
	addAttr -ci true -k true -sn "list_switch_name" -ln "list_switch_name" -dt "stringArray";
	addAttr -ci true -k true -sn "fk_space_switch" -ln "fk_space_switch" -min 0 -max 
		1 -at "bool";
	addAttr -ci true -k true -sn "list_fk_switch_target" -ln "list_fk_switch_target" 
		-dt "stringArray";
	addAttr -ci true -k true -sn "list_fk_switch_name" -ln "list_fk_switch_name" -dt "stringArray";
	addAttr -ci true -k true -sn "enable_wrist_corrective" -ln "enable_wrist_corrective" 
		-min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "list_wrist_joint" -ln "list_wrist_joint" -dt "stringArray";
	addAttr -ci true -k true -sn "wrist_corrective_axis_push" -ln "wrist_corrective_axis_push" 
		-min 0 -max 5 -en "X:Y:Z:-X:-Y:-Z" -at "enum";
	addAttr -ci true -k true -sn "wrist_axis" -ln "wrist_axis" -min 0 -max 5 -en "xyz:xzy:yxz:yzx:zyx:zxy" 
		-at "enum";
	addAttr -ci true -k true -sn "wrist_corrective_front_invert" -ln "wrist_corrective_front_invert" 
		-min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "wrist_corrective_upper_invert" -ln "wrist_corrective_upper_invert" 
		-min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "wrist_corrective_back_invert" -ln "wrist_corrective_back_invert" 
		-min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "wrist_corrective_lower_invert" -ln "wrist_corrective_lower_invert" 
		-min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "enable_elbow_corrective" -ln "enable_elbow_corrective" 
		-min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "list_elbow_joint" -ln "list_elbow_joint" -dt "stringArray";
	addAttr -ci true -k true -sn "elbow_corrective_axis_push" -ln "elbow_corrective_axis_push" 
		-min 0 -max 5 -en "X:Y:Z:-X:-Y:-Z" -at "enum";
	addAttr -ci true -k true -sn "elbow_axis" -ln "elbow_axis" -min 0 -max 5 -en "xyz:xzy:yxz:yzx:zyx:zxy" 
		-at "enum";
	addAttr -ci true -k true -sn "enable_shoulder_corrective" -ln "enable_shoulder_corrective" 
		-min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "list_shoulder_joint" -ln "list_shoulder_joint" -dt "stringArray";
	addAttr -ci true -k true -sn "shoulder_corrective_axis_push" -ln "shoulder_corrective_axis_push" 
		-min 0 -max 5 -en "X:Y:Z:-X:-Y:-Z" -at "enum";
	addAttr -ci true -k true -sn "shoulder_axis" -ln "shoulder_axis" -min 0 -max 5 -en 
		"xyz:xzy:yxz:yzx:zyx:zxy" -at "enum";
	addAttr -ci true -k true -sn "shoulder_corrective_invert" -ln "shoulder_corrective_invert" 
		-min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "auto_setup_ribbon_upper_joint" -ln "auto_setup_ribbon_upper_joint" 
		-min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "auto_setup_ribbon_lower_joint" -ln "auto_setup_ribbon_lower_joint" 
		-min 0 -max 1 -at "bool";
	setAttr -k on ".name" -type "string" "LFT_leg";
	setAttr -k on ".enable" yes;
	setAttr -k on ".class" -type "string" "EasySkeleton.rigs.BodyGlobal.Limb";
	setAttr -k on ".parent" -type "string" "pelvis";
	setAttr -k on ".control_scale" 0.40000000596046448;
	setAttr -k on ".list_limb_joint" -type "stringArray" 3 "LFT_legUp" "LFT_legLow" "LFT_ankle"  ;
	setAttr -k on ".axis_forward" 1;
	setAttr -k on ".axis_pole" 5;
	setAttr -k on ".pole_distance" 10;
	setAttr -k on ".jnt_ball" -type "string" "LFT_ball";
	setAttr -k on ".jnt_clavicle" -type "string" "";
	setAttr -k on ".use_world_pole" yes;
	setAttr -k on ".world_direction_pole" 2;
	setAttr -k on ".list_ik_pivot" -type "stringArray" 4 "LFT_innerFootPiv" "LFT_outerFootPiv" "LFT_heelFootPiv" "LFT_endFootPiv"  ;
	setAttr -k on ".jnt_tip" -type "string" "LFT_toe";
	setAttr -k on ".ik_base_axis" 2;
	setAttr -k on ".auto_roll_default_value" 25;
	setAttr -k on ".list_low_ribbon_joint" -type "stringArray" 0  ;
	setAttr -k on ".list_up_ribbon_joint" -type "stringArray" 0  ;
	setAttr -k on ".enable_ribbon_up_twist" yes;
	setAttr -k on ".enable_ribbon_low_twist" yes;
	setAttr -k on ".ik_pivot_enable" yes;
	setAttr -k on ".invert_roll_value" yes;
	setAttr -k on ".invert_roll_axis" yes;
	setAttr -k on ".default_switch" 1;
	setAttr -k on ".list_clavicle_switch_target" -type "stringArray" 0  ;
	setAttr -k on ".list_clavicle_switch_name" -type "stringArray" 0  ;
	setAttr -k on ".list_switch_target" -type "stringArray" 0  ;
	setAttr -k on ".list_switch_name" -type "stringArray" 0  ;
	setAttr -k on ".fk_space_switch" yes;
	setAttr -k on ".list_fk_switch_target" -type "stringArray" 3 "pelvis" "root" "rootLoc"  ;
	setAttr -k on ".list_fk_switch_name" -type "stringArray" 3 "Pelvis" "Cog" "World"  ;
	setAttr -k on ".list_wrist_joint" -type "stringArray" 0  ;
	setAttr -k on ".wrist_corrective_front_invert" yes;
	setAttr -k on ".wrist_corrective_upper_invert" yes;
	setAttr -k on ".list_elbow_joint" -type "stringArray" 0  ;
	setAttr -k on ".list_shoulder_joint" -type "stringArray" 0  ;
createNode network -n "RGT_arm";
	rename -uid "878FD493-4DBA-4FE6-1B8F-F9B634D396C3";
	addAttr -ci true -k true -sn "name" -ln "name" -dt "string";
	addAttr -ci true -k true -sn "enable" -ln "enable" -min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "isBuild" -ln "isBuild" -min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "class" -ln "class" -dt "string";
	addAttr -ci true -k true -sn "parent" -ln "parent" -dt "string";
	addAttr -ci true -k true -sn "control_scale" -ln "control_scale" -min 0 -max 1 -at "float";
	addAttr -ci true -k true -sn "debug_mode" -ln "debug_mode" -min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "mirror_control_scale" -ln "mirror_control_scale" -min 
		0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "list_limb_joint" -ln "list_limb_joint" -dt "stringArray";
	addAttr -ci true -k true -sn "axis_forward" -ln "axis_forward" -min 0 -max 5 -en 
		"X:Y:Z:-X:-Y:-Z" -at "enum";
	addAttr -ci true -k true -sn "axis_pole" -ln "axis_pole" -min 0 -max 5 -en "X:Y:Z:-X:-Y:-Z" 
		-at "enum";
	addAttr -ci true -k true -sn "attribute_switch_range" -ln "attribute_switch_range" 
		-min 0 -max 1 -en "1:10" -at "enum";
	addAttr -ci true -k true -sn "pole_distance" -ln "pole_distance" -dv 5 -at "float";
	addAttr -ci true -k true -sn "jnt_ball" -ln "jnt_ball" -dt "string";
	addAttr -ci true -k true -sn "clavicle_enable" -ln "clavicle_enable" -min 0 -max 
		1 -at "bool";
	addAttr -ci true -k true -sn "jnt_clavicle" -ln "jnt_clavicle" -dt "string";
	addAttr -ci true -k true -sn "use_world_pole" -ln "use_world_pole" -min 0 -max 1 
		-at "bool";
	addAttr -ci true -k true -sn "world_direction_pole" -ln "world_direction_pole" -min 
		0 -max 2 -en "X:Y:Z" -at "enum";
	addAttr -ci true -k true -sn "stretch_with_fixed_angle" -ln "stretch_with_fixed_angle" 
		-min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "use_custom_fixed_angle_percentage" -ln "use_custom_fixed_angle_percentage" 
		-min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "custom_fixed_percentage" -ln "custom_fixed_percentage" 
		-at "long";
	addAttr -ci true -k true -sn "list_ik_pivot" -ln "list_ik_pivot" -dt "stringArray";
	addAttr -ci true -k true -sn "jnt_tip" -ln "jnt_tip" -dt "string";
	addAttr -ci true -k true -sn "ik_base_axis" -ln "ik_base_axis" -min 0 -max 5 -en 
		"xyz:xzy:yxz:yzx:zyx:zxy" -at "enum";
	addAttr -ci true -k true -sn "auto_roll_default_value" -ln "auto_roll_default_value" 
		-at "float";
	addAttr -ci true -k true -sn "ribbon_up_enable" -ln "ribbon_up_enable" -min 0 -max 
		1 -at "bool";
	addAttr -ci true -k true -sn "ribbon_low_enable" -ln "ribbon_low_enable" -min 0 
		-max 1 -at "bool";
	addAttr -ci true -k true -sn "list_low_ribbon_joint" -ln "list_low_ribbon_joint" 
		-dt "stringArray";
	addAttr -ci true -k true -sn "list_up_ribbon_joint" -ln "list_up_ribbon_joint" -dt "stringArray";
	addAttr -ci true -k true -sn "enable_ribbon_up_twist" -ln "enable_ribbon_up_twist" 
		-min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "enable_ribbon_low_twist" -ln "enable_ribbon_low_twist" 
		-min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "ik_pivot_enable" -ln "ik_pivot_enable" -min 0 -max 
		1 -at "bool";
	addAttr -ci true -k true -sn "invert_roll_value" -ln "invert_roll_value" -min 0 
		-max 1 -at "bool";
	addAttr -ci true -k true -sn "invert_side_roll_value" -ln "invert_side_roll_value" 
		-min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "invert_toe_twist_value" -ln "invert_toe_twist_value" 
		-min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "invert_middle_twist_value" -ln "invert_middle_twist_value" 
		-min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "invert_heel_twist_value" -ln "invert_heel_twist_value" 
		-min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "invert_roll_axis" -ln "invert_roll_axis" -min 0 -max 
		1 -at "bool";
	addAttr -ci true -k true -sn "invert_roll_side_axis" -ln "invert_roll_side_axis" 
		-min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "default_switch" -ln "default_switch" -min 0 -max 1 
		-en "FK:IK" -at "enum";
	addAttr -ci true -k true -sn "clavicle_space_switch" -ln "clavicle_space_switch" 
		-min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "list_clavicle_switch_target" -ln "list_clavicle_switch_target" 
		-dt "stringArray";
	addAttr -ci true -k true -sn "list_clavicle_switch_name" -ln "list_clavicle_switch_name" 
		-dt "stringArray";
	addAttr -ci true -k true -sn "hand_space_switch" -ln "hand_space_switch" -min 0 
		-max 1 -at "bool";
	addAttr -ci true -k true -sn "list_switch_target" -ln "list_switch_target" -dt "stringArray";
	addAttr -ci true -k true -sn "list_switch_name" -ln "list_switch_name" -dt "stringArray";
	addAttr -ci true -k true -sn "fk_space_switch" -ln "fk_space_switch" -min 0 -max 
		1 -at "bool";
	addAttr -ci true -k true -sn "list_fk_switch_target" -ln "list_fk_switch_target" 
		-dt "stringArray";
	addAttr -ci true -k true -sn "list_fk_switch_name" -ln "list_fk_switch_name" -dt "stringArray";
	addAttr -ci true -k true -sn "enable_wrist_corrective" -ln "enable_wrist_corrective" 
		-min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "list_wrist_joint" -ln "list_wrist_joint" -dt "stringArray";
	addAttr -ci true -k true -sn "wrist_corrective_axis_push" -ln "wrist_corrective_axis_push" 
		-min 0 -max 5 -en "X:Y:Z:-X:-Y:-Z" -at "enum";
	addAttr -ci true -k true -sn "wrist_axis" -ln "wrist_axis" -min 0 -max 5 -en "xyz:xzy:yxz:yzx:zyx:zxy" 
		-at "enum";
	addAttr -ci true -k true -sn "wrist_corrective_front_invert" -ln "wrist_corrective_front_invert" 
		-min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "wrist_corrective_upper_invert" -ln "wrist_corrective_upper_invert" 
		-min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "wrist_corrective_back_invert" -ln "wrist_corrective_back_invert" 
		-min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "wrist_corrective_lower_invert" -ln "wrist_corrective_lower_invert" 
		-min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "enable_elbow_corrective" -ln "enable_elbow_corrective" 
		-min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "list_elbow_joint" -ln "list_elbow_joint" -dt "stringArray";
	addAttr -ci true -k true -sn "elbow_corrective_axis_push" -ln "elbow_corrective_axis_push" 
		-min 0 -max 5 -en "X:Y:Z:-X:-Y:-Z" -at "enum";
	addAttr -ci true -k true -sn "elbow_axis" -ln "elbow_axis" -min 0 -max 5 -en "xyz:xzy:yxz:yzx:zyx:zxy" 
		-at "enum";
	addAttr -ci true -k true -sn "enable_shoulder_corrective" -ln "enable_shoulder_corrective" 
		-min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "list_shoulder_joint" -ln "list_shoulder_joint" -dt "stringArray";
	addAttr -ci true -k true -sn "shoulder_corrective_axis_push" -ln "shoulder_corrective_axis_push" 
		-min 0 -max 5 -en "X:Y:Z:-X:-Y:-Z" -at "enum";
	addAttr -ci true -k true -sn "shoulder_axis" -ln "shoulder_axis" -min 0 -max 5 -en 
		"xyz:xzy:yxz:yzx:zyx:zxy" -at "enum";
	addAttr -ci true -k true -sn "shoulder_corrective_invert" -ln "shoulder_corrective_invert" 
		-min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "auto_setup_ribbon_upper_joint" -ln "auto_setup_ribbon_upper_joint" 
		-min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "auto_setup_ribbon_lower_joint" -ln "auto_setup_ribbon_lower_joint" 
		-min 0 -max 1 -at "bool";
	setAttr -k on ".name" -type "string" "RGT_arm";
	setAttr -k on ".enable" yes;
	setAttr -k on ".class" -type "string" "EasySkeleton.rigs.BodyGlobal.Limb";
	setAttr -k on ".parent" -type "string" "spine4";
	setAttr -k on ".control_scale" 0.40000000596046448;
	setAttr -k on ".mirror_control_scale" yes;
	setAttr -k on ".list_limb_joint" -type "stringArray" 3 "RGT_armUp" "RGT_armLow" "RGT_hand"  ;
	setAttr -k on ".axis_forward" 4;
	setAttr -k on ".axis_pole" 3;
	setAttr -k on ".pole_distance" -10;
	setAttr -k on ".jnt_ball" -type "string" "";
	setAttr -k on ".clavicle_enable" yes;
	setAttr -k on ".jnt_clavicle" -type "string" "RGT_clavicle";
	setAttr -k on ".use_world_pole" yes;
	setAttr -k on ".world_direction_pole" 2;
	setAttr -k on ".list_ik_pivot" -type "stringArray" 0  ;
	setAttr -k on ".jnt_tip" -type "string" "";
	setAttr -k on ".list_low_ribbon_joint" -type "stringArray" 0  ;
	setAttr -k on ".list_up_ribbon_joint" -type "stringArray" 0  ;
	setAttr -k on ".enable_ribbon_up_twist" yes;
	setAttr -k on ".enable_ribbon_low_twist" yes;
	setAttr -k on ".list_clavicle_switch_target" -type "stringArray" 0  ;
	setAttr -k on ".list_clavicle_switch_name" -type "stringArray" 0  ;
	setAttr -k on ".hand_space_switch" yes;
	setAttr -k on ".list_switch_target" -type "stringArray" 5 "rootLoc" "root" "pelvis" "spine4" "head"  ;
	setAttr -k on ".list_switch_name" -type "stringArray" 5 "World" "Cog" "Pelvis" "Chest" "Head"  ;
	setAttr -k on ".fk_space_switch" yes;
	setAttr -k on ".list_fk_switch_target" -type "stringArray" 4 "RGT_clavicle" "spine4" "root" "rootLoc"  ;
	setAttr -k on ".list_fk_switch_name" -type "stringArray" 4 "Clavicle" "Chest" "Cog" "World"  ;
	setAttr -k on ".list_wrist_joint" -type "stringArray" 0  ;
	setAttr -k on ".wrist_corrective_front_invert" yes;
	setAttr -k on ".wrist_corrective_upper_invert" yes;
	setAttr -k on ".list_elbow_joint" -type "stringArray" 0  ;
	setAttr -k on ".list_shoulder_joint" -type "stringArray" 0  ;
createNode network -n "RGT_leg";
	rename -uid "27193D14-4BC8-5B40-9FCC-DD89DDEF1D1B";
	addAttr -ci true -k true -sn "name" -ln "name" -dt "string";
	addAttr -ci true -k true -sn "enable" -ln "enable" -min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "isBuild" -ln "isBuild" -min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "class" -ln "class" -dt "string";
	addAttr -ci true -k true -sn "parent" -ln "parent" -dt "string";
	addAttr -ci true -k true -sn "control_scale" -ln "control_scale" -min 0 -max 1 -at "float";
	addAttr -ci true -k true -sn "debug_mode" -ln "debug_mode" -min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "mirror_control_scale" -ln "mirror_control_scale" -min 
		0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "list_limb_joint" -ln "list_limb_joint" -dt "stringArray";
	addAttr -ci true -k true -sn "axis_forward" -ln "axis_forward" -min 0 -max 5 -en 
		"X:Y:Z:-X:-Y:-Z" -at "enum";
	addAttr -ci true -k true -sn "axis_pole" -ln "axis_pole" -min 0 -max 5 -en "X:Y:Z:-X:-Y:-Z" 
		-at "enum";
	addAttr -ci true -k true -sn "attribute_switch_range" -ln "attribute_switch_range" 
		-min 0 -max 1 -en "1:10" -at "enum";
	addAttr -ci true -k true -sn "pole_distance" -ln "pole_distance" -dv 5 -at "float";
	addAttr -ci true -k true -sn "jnt_ball" -ln "jnt_ball" -dt "string";
	addAttr -ci true -k true -sn "clavicle_enable" -ln "clavicle_enable" -min 0 -max 
		1 -at "bool";
	addAttr -ci true -k true -sn "jnt_clavicle" -ln "jnt_clavicle" -dt "string";
	addAttr -ci true -k true -sn "use_world_pole" -ln "use_world_pole" -min 0 -max 1 
		-at "bool";
	addAttr -ci true -k true -sn "world_direction_pole" -ln "world_direction_pole" -min 
		0 -max 2 -en "X:Y:Z" -at "enum";
	addAttr -ci true -k true -sn "stretch_with_fixed_angle" -ln "stretch_with_fixed_angle" 
		-min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "use_custom_fixed_angle_percentage" -ln "use_custom_fixed_angle_percentage" 
		-min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "custom_fixed_percentage" -ln "custom_fixed_percentage" 
		-at "long";
	addAttr -ci true -k true -sn "list_ik_pivot" -ln "list_ik_pivot" -dt "stringArray";
	addAttr -ci true -k true -sn "jnt_tip" -ln "jnt_tip" -dt "string";
	addAttr -ci true -k true -sn "ik_base_axis" -ln "ik_base_axis" -min 0 -max 5 -en 
		"xyz:xzy:yxz:yzx:zyx:zxy" -at "enum";
	addAttr -ci true -k true -sn "auto_roll_default_value" -ln "auto_roll_default_value" 
		-at "float";
	addAttr -ci true -k true -sn "ribbon_up_enable" -ln "ribbon_up_enable" -min 0 -max 
		1 -at "bool";
	addAttr -ci true -k true -sn "ribbon_low_enable" -ln "ribbon_low_enable" -min 0 
		-max 1 -at "bool";
	addAttr -ci true -k true -sn "list_low_ribbon_joint" -ln "list_low_ribbon_joint" 
		-dt "stringArray";
	addAttr -ci true -k true -sn "list_up_ribbon_joint" -ln "list_up_ribbon_joint" -dt "stringArray";
	addAttr -ci true -k true -sn "enable_ribbon_up_twist" -ln "enable_ribbon_up_twist" 
		-min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "enable_ribbon_low_twist" -ln "enable_ribbon_low_twist" 
		-min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "ik_pivot_enable" -ln "ik_pivot_enable" -min 0 -max 
		1 -at "bool";
	addAttr -ci true -k true -sn "invert_roll_value" -ln "invert_roll_value" -min 0 
		-max 1 -at "bool";
	addAttr -ci true -k true -sn "invert_side_roll_value" -ln "invert_side_roll_value" 
		-min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "invert_toe_twist_value" -ln "invert_toe_twist_value" 
		-min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "invert_middle_twist_value" -ln "invert_middle_twist_value" 
		-min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "invert_heel_twist_value" -ln "invert_heel_twist_value" 
		-min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "invert_roll_axis" -ln "invert_roll_axis" -min 0 -max 
		1 -at "bool";
	addAttr -ci true -k true -sn "invert_roll_side_axis" -ln "invert_roll_side_axis" 
		-min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "default_switch" -ln "default_switch" -min 0 -max 1 
		-en "FK:IK" -at "enum";
	addAttr -ci true -k true -sn "clavicle_space_switch" -ln "clavicle_space_switch" 
		-min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "list_clavicle_switch_target" -ln "list_clavicle_switch_target" 
		-dt "stringArray";
	addAttr -ci true -k true -sn "list_clavicle_switch_name" -ln "list_clavicle_switch_name" 
		-dt "stringArray";
	addAttr -ci true -k true -sn "hand_space_switch" -ln "hand_space_switch" -min 0 
		-max 1 -at "bool";
	addAttr -ci true -k true -sn "list_switch_target" -ln "list_switch_target" -dt "stringArray";
	addAttr -ci true -k true -sn "list_switch_name" -ln "list_switch_name" -dt "stringArray";
	addAttr -ci true -k true -sn "fk_space_switch" -ln "fk_space_switch" -min 0 -max 
		1 -at "bool";
	addAttr -ci true -k true -sn "list_fk_switch_target" -ln "list_fk_switch_target" 
		-dt "stringArray";
	addAttr -ci true -k true -sn "list_fk_switch_name" -ln "list_fk_switch_name" -dt "stringArray";
	addAttr -ci true -k true -sn "enable_wrist_corrective" -ln "enable_wrist_corrective" 
		-min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "list_wrist_joint" -ln "list_wrist_joint" -dt "stringArray";
	addAttr -ci true -k true -sn "wrist_corrective_axis_push" -ln "wrist_corrective_axis_push" 
		-min 0 -max 5 -en "X:Y:Z:-X:-Y:-Z" -at "enum";
	addAttr -ci true -k true -sn "wrist_axis" -ln "wrist_axis" -min 0 -max 5 -en "xyz:xzy:yxz:yzx:zyx:zxy" 
		-at "enum";
	addAttr -ci true -k true -sn "wrist_corrective_front_invert" -ln "wrist_corrective_front_invert" 
		-min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "wrist_corrective_upper_invert" -ln "wrist_corrective_upper_invert" 
		-min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "wrist_corrective_back_invert" -ln "wrist_corrective_back_invert" 
		-min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "wrist_corrective_lower_invert" -ln "wrist_corrective_lower_invert" 
		-min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "enable_elbow_corrective" -ln "enable_elbow_corrective" 
		-min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "list_elbow_joint" -ln "list_elbow_joint" -dt "stringArray";
	addAttr -ci true -k true -sn "elbow_corrective_axis_push" -ln "elbow_corrective_axis_push" 
		-min 0 -max 5 -en "X:Y:Z:-X:-Y:-Z" -at "enum";
	addAttr -ci true -k true -sn "elbow_axis" -ln "elbow_axis" -min 0 -max 5 -en "xyz:xzy:yxz:yzx:zyx:zxy" 
		-at "enum";
	addAttr -ci true -k true -sn "enable_shoulder_corrective" -ln "enable_shoulder_corrective" 
		-min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "list_shoulder_joint" -ln "list_shoulder_joint" -dt "stringArray";
	addAttr -ci true -k true -sn "shoulder_corrective_axis_push" -ln "shoulder_corrective_axis_push" 
		-min 0 -max 5 -en "X:Y:Z:-X:-Y:-Z" -at "enum";
	addAttr -ci true -k true -sn "shoulder_axis" -ln "shoulder_axis" -min 0 -max 5 -en 
		"xyz:xzy:yxz:yzx:zyx:zxy" -at "enum";
	addAttr -ci true -k true -sn "shoulder_corrective_invert" -ln "shoulder_corrective_invert" 
		-min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "auto_setup_ribbon_upper_joint" -ln "auto_setup_ribbon_upper_joint" 
		-min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "auto_setup_ribbon_lower_joint" -ln "auto_setup_ribbon_lower_joint" 
		-min 0 -max 1 -at "bool";
	setAttr -k on ".name" -type "string" "RGT_leg";
	setAttr -k on ".enable" yes;
	setAttr -k on ".class" -type "string" "EasySkeleton.rigs.BodyGlobal.Limb";
	setAttr -k on ".parent" -type "string" "pelvis";
	setAttr -k on ".control_scale" 0.40000000596046448;
	setAttr -k on ".mirror_control_scale" yes;
	setAttr -k on ".list_limb_joint" -type "stringArray" 3 "RGT_legUp" "RGT_legLow" "RGT_ankle"  ;
	setAttr -k on ".axis_forward" 4;
	setAttr -k on ".axis_pole" 2;
	setAttr -k on ".pole_distance" 10;
	setAttr -k on ".jnt_ball" -type "string" "RGT_ball";
	setAttr -k on ".jnt_clavicle" -type "string" "";
	setAttr -k on ".use_world_pole" yes;
	setAttr -k on ".world_direction_pole" 2;
	setAttr -k on ".list_ik_pivot" -type "stringArray" 4 "RGT_innerFootPiv" "RGT_outerFootPiv" "RGT_heelFootPiv" "RGT_endFootPiv"  ;
	setAttr -k on ".jnt_tip" -type "string" "RGT_toe";
	setAttr -k on ".ik_base_axis" 2;
	setAttr -k on ".auto_roll_default_value" 25;
	setAttr -k on ".list_low_ribbon_joint" -type "stringArray" 0  ;
	setAttr -k on ".list_up_ribbon_joint" -type "stringArray" 0  ;
	setAttr -k on ".enable_ribbon_up_twist" yes;
	setAttr -k on ".enable_ribbon_low_twist" yes;
	setAttr -k on ".ik_pivot_enable" yes;
	setAttr -k on ".invert_roll_value" yes;
	setAttr -k on ".invert_roll_axis" yes;
	setAttr -k on ".default_switch" 1;
	setAttr -k on ".list_clavicle_switch_target" -type "stringArray" 0  ;
	setAttr -k on ".list_clavicle_switch_name" -type "stringArray" 0  ;
	setAttr -k on ".list_switch_target" -type "stringArray" 0  ;
	setAttr -k on ".list_switch_name" -type "stringArray" 0  ;
	setAttr -k on ".fk_space_switch" yes;
	setAttr -k on ".list_fk_switch_target" -type "stringArray" 3 "pelvis" "root" "rootLoc"  ;
	setAttr -k on ".list_fk_switch_name" -type "stringArray" 3 "Pelvis" "Cog" "World"  ;
	setAttr -k on ".list_wrist_joint" -type "stringArray" 0  ;
	setAttr -k on ".wrist_corrective_front_invert" yes;
	setAttr -k on ".wrist_corrective_upper_invert" yes;
	setAttr -k on ".list_elbow_joint" -type "stringArray" 0  ;
	setAttr -k on ".list_shoulder_joint" -type "stringArray" 0  ;
createNode network -n "Torso";
	rename -uid "AEF6B383-41DF-8B7C-82D6-C4B80487783D";
	addAttr -ci true -k true -sn "name" -ln "name" -dt "string";
	addAttr -ci true -k true -sn "enable" -ln "enable" -min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "isBuild" -ln "isBuild" -min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "class" -ln "class" -dt "string";
	addAttr -ci true -k true -sn "parent" -ln "parent" -dt "string";
	addAttr -ci true -k true -sn "control_scale" -ln "control_scale" -min 0 -max 1 -at "float";
	addAttr -ci true -k true -sn "debug_mode" -ln "debug_mode" -min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "mirror_control_scale" -ln "mirror_control_scale" -min 
		0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "list_joint_spine" -ln "list_joint_spine" -dt "stringArray";
	addAttr -ci true -k true -sn "list_fk_control_pivot" -ln "list_fk_control_pivot" 
		-dt "stringArray";
	addAttr -ci true -k true -sn "ribbon_fk_weight" -ln "ribbon_fk_weight" -dt "string";
	addAttr -ci true -k true -sn "ribbon_ik_weight" -ln "ribbon_ik_weight" -dt "string";
	addAttr -ci true -k true -sn "ribbon_output_weight" -ln "ribbon_output_weight" -dt "string";
	addAttr -ci true -k true -sn "cog_pivot" -ln "cog_pivot" -dt "string";
	addAttr -ci true -k true -sn "use_root_joint_as_pivot" -ln "use_root_joint_as_pivot" 
		-min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "locator_ik_chest_position" -ln "locator_ik_chest_position" 
		-dt "string";
	addAttr -ci true -k true -sn "list_scalable_volume_joint" -ln "list_scalable_volume_joint" 
		-dt "stringArray";
	addAttr -ci true -k true -sn "enable_breath_scale" -ln "enable_breath_scale" -min 
		0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "jnt_breath_scale" -ln "jnt_breath_scale" -dt "string";
	addAttr -ci true -k true -sn "axis_direction" -ln "axis_direction" -min 0 -max 5 
		-en "xyz:xzy:yxz:yzx:zyx:zxy" -at "enum";
	addAttr -ci true -k true -sn "enable_auto_volume_as_default" -ln "enable_auto_volume_as_default" 
		-min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "ribbon_ik_middle_weight" -ln "ribbon_ik_middle_weight" 
		-dt "string";
	addAttr -ci true -k true -sn "enable_breast_rig" -ln "enable_breast_rig" -min 0 
		-max 1 -at "bool";
	addAttr -ci true -k true -sn "L_list_jnt_breast" -ln "L_list_jnt_breast" -dt "stringArray";
	addAttr -ci true -k true -sn "R_list_jnt_breast" -ln "R_list_jnt_breast" -dt "stringArray";
	addAttr -ci true -k true -sn "enable_auto_spine_scale" -ln "enable_auto_spine_scale" 
		-min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "auto_volume_influence_detect" -ln "auto_volume_influence_detect" 
		-min 0 -max 1 -en "Ik Only:Ik and Fk" -at "enum";
	addAttr -ci true -k true -sn "quick_create_guide" -ln "quick_create_guide" -min 
		0 -max 1 -at "bool";
	setAttr -k on ".name" -type "string" "Torso";
	setAttr -k on ".enable" yes;
	setAttr -k on ".class" -type "string" "EasySkeleton.rigs.BodyGlobal.TorsoRibbon";
	setAttr -k on ".parent";
	setAttr -k on ".control_scale" 0.40000000596046448;
	setAttr -k on ".list_joint_spine" -type "stringArray" 5 "pelvis" "spine1" "spine2" "spine3" "spine4"  ;
	setAttr -k on ".list_fk_control_pivot" -type "stringArray" 5 "loc_fk_torso1" "loc_fk_torso2" "loc_fk_torso3" "loc_fk_torso4" "loc_fk_torso5"  ;
	setAttr -k on ".ribbon_fk_weight" -type "string" "";
	setAttr -k on ".ribbon_ik_weight" -type "string" "";
	setAttr -k on ".ribbon_output_weight" -type "string" "";
	setAttr -k on ".cog_pivot" -type "string" "root";
	setAttr -k on ".use_root_joint_as_pivot" yes;
	setAttr -k on ".locator_ik_chest_position" -type "string" "loc_ik_torso";
	setAttr -k on ".list_scalable_volume_joint" -type "stringArray" 3 "spine1" "spine2" "spine3"  ;
	setAttr -k on ".jnt_breath_scale" -type "string" "";
	setAttr -k on ".axis_direction" 2;
	setAttr -k on ".enable_auto_volume_as_default" yes;
	setAttr -k on ".ribbon_ik_middle_weight" -type "string" "";
	setAttr -k on ".L_list_jnt_breast" -type "stringArray" 0  ;
	setAttr -k on ".R_list_jnt_breast" -type "stringArray" 0  ;
createNode network -n "Head";
	rename -uid "A46A407C-4FEF-9387-CA47-C28CBB1782AF";
	addAttr -ci true -k true -sn "name" -ln "name" -dt "string";
	addAttr -ci true -k true -sn "enable" -ln "enable" -min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "isBuild" -ln "isBuild" -min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "class" -ln "class" -dt "string";
	addAttr -ci true -k true -sn "parent" -ln "parent" -dt "string";
	addAttr -ci true -k true -sn "control_scale" -ln "control_scale" -min 0 -max 1 -at "float";
	addAttr -ci true -k true -sn "debug_mode" -ln "debug_mode" -min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "mirror_control_scale" -ln "mirror_control_scale" -min 
		0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "list_head_joints" -ln "list_head_joints" -dt "stringArray";
	addAttr -ci true -k true -sn "axis_forward" -ln "axis_forward" -min 0 -max 2 -en 
		"X:Y:Z" -at "enum";
	addAttr -ci true -k true -sn "enable_squash_head" -ln "enable_squash_head" -min 
		0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "list_head_squash_joint" -ln "list_head_squash_joint" 
		-dt "stringArray";
	addAttr -ci true -k true -sn "list_head_squash_handle_piv" -ln "list_head_squash_handle_piv" 
		-dt "stringArray";
	addAttr -ci true -k true -sn "follow_intensity" -ln "follow_intensity" -dv 1 -at "float";
	setAttr -k on ".name" -type "string" "Head";
	setAttr -k on ".enable" yes;
	setAttr -k on ".class" -type "string" "EasySkeleton.rigs.BodyGlobal.Head";
	setAttr -k on ".parent" -type "string" "spine4";
	setAttr -k on ".control_scale" 0.40000000596046448;
	setAttr -k on ".list_head_joints" -type "stringArray" 3 "neck1" "neck2" "head"  ;
	setAttr -k on ".axis_forward" 1;
	setAttr -k on ".list_head_squash_joint" -type "stringArray" 0  ;
	setAttr -k on ".list_head_squash_handle_piv" -type "stringArray" 0  ;
createNode script -n "uiConfigurationScriptNode";
	rename -uid "2CDBC6F4-4C7B-7EBB-837C-89B304272AF4";
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
		+ "            -fluids 1\n            -hairSystems 1\n            -follicles 1\n            -nCloths 1\n            -nParticles 1\n            -nRigids 1\n            -dynamicConstraints 1\n            -locators 1\n            -manipulators 1\n            -pluginShapes 1\n            -dimensions 1\n            -handles 1\n            -pivots 1\n            -textures 1\n            -strokes 1\n            -motionTrails 1\n            -clipGhosts 1\n            -greasePencils 1\n            -shadows 0\n            -captureSequenceNumber -1\n            -width 1180\n            -height 928\n            -sceneRenderFilter 0\n            -activeShadingGraph \"ballora_animatronic_shadow_rig:rsMaterial1SG,ballora_animatronic_shadow_rig:MAT_ballora,ballora_animatronic_shadow_rig:MAT_ballora\" \n            -activeCustomGeometry \"meshShaderball\" \n            $editorName;\n        modelEditor -e -viewSelected 0 $editorName;\n        modelEditor -e \n            -pluginObjects \"gpuCacheDisplayFilter\" 1 \n            $editorName;\n\t\tif (!$useSceneConfig) {\n"
		+ "\t\t\tpanel -e -l $label $panelName;\n\t\t}\n\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextPanel \"outlinerPanel\" (localizedPanelLabel(\"Outliner\")) `;\n\tif (\"\" != $panelName) {\n\t\t$label = `panel -q -label $panelName`;\n\t\toutlinerPanel -edit -l (localizedPanelLabel(\"Outliner\")) -mbv $menusOkayInPanels  $panelName;\n\t\t$editorName = $panelName;\n        outlinerEditor -e \n            -docTag \"isolOutln_fromSeln\" \n            -showShapes 0\n            -showAssignedMaterials 0\n            -showTimeEditor 1\n            -showReferenceNodes 0\n            -showReferenceMembers 0\n            -showAttributes 0\n            -showConnected 0\n            -showAnimCurvesOnly 0\n            -showMuteInfo 0\n            -organizeByLayer 1\n            -organizeByClip 1\n            -showAnimLayerWeight 1\n            -autoExpandLayers 1\n            -autoExpand 0\n            -showDagOnly 1\n            -showAssets 1\n            -showContainedOnly 1\n            -showPublishedAsConnected 0\n            -showParentContainers 0\n            -showContainerContents 1\n"
		+ "            -ignoreDagHierarchy 0\n            -expandConnections 0\n            -showUpstreamCurves 1\n            -showUnitlessCurves 1\n            -showCompounds 1\n            -showLeafs 1\n            -showNumericAttrsOnly 0\n            -highlightActive 1\n            -autoSelectNewObjects 0\n            -doNotSelectNewObjects 0\n            -dropIsParent 1\n            -transmitFilters 0\n            -setFilter \"defaultSetFilter\" \n            -showSetMembers 1\n            -allowMultiSelection 1\n            -alwaysToggleSelect 0\n            -directSelect 0\n            -isSet 0\n            -isSetMember 0\n            -displayMode \"DAG\" \n            -expandObjects 0\n            -setsIgnoreFilters 1\n            -containersIgnoreFilters 0\n            -editAttrName 0\n            -showAttrValues 0\n            -highlightSecondary 0\n            -showUVAttrsOnly 0\n            -showTextureNodesOnly 0\n            -attrAlphaOrder \"default\" \n            -animLayerFilterOptions \"allAffecting\" \n            -sortOrder \"none\" \n            -longNames 0\n"
		+ "            -niceNames 1\n            -selectCommand \"print(\\\"\\\")\" \n            -showNamespace 1\n            -showPinIcons 0\n            -mapMotionTrails 0\n            -ignoreHiddenAttribute 0\n            -ignoreOutlinerColor 0\n            -renderFilterVisible 0\n            -renderFilterIndex 0\n            -selectionOrder \"chronological\" \n            -expandAttribute 0\n            $editorName;\n\t\tif (!$useSceneConfig) {\n\t\t\tpanel -e -l $label $panelName;\n\t\t}\n\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextPanel \"outlinerPanel\" (localizedPanelLabel(\"Outliner\")) `;\n\tif (\"\" != $panelName) {\n\t\t$label = `panel -q -label $panelName`;\n\t\toutlinerPanel -edit -l (localizedPanelLabel(\"Outliner\")) -mbv $menusOkayInPanels  $panelName;\n\t\t$editorName = $panelName;\n        outlinerEditor -e \n            -docTag \"isolOutln_fromSeln\" \n            -showShapes 0\n            -showAssignedMaterials 0\n            -showTimeEditor 1\n            -showReferenceNodes 0\n            -showReferenceMembers 0\n            -showAttributes 0\n            -showConnected 0\n"
		+ "            -showAnimCurvesOnly 0\n            -showMuteInfo 0\n            -organizeByLayer 1\n            -organizeByClip 1\n            -showAnimLayerWeight 1\n            -autoExpandLayers 1\n            -autoExpand 0\n            -showDagOnly 1\n            -showAssets 1\n            -showContainedOnly 1\n            -showPublishedAsConnected 0\n            -showParentContainers 0\n            -showContainerContents 1\n            -ignoreDagHierarchy 0\n            -expandConnections 0\n            -showUpstreamCurves 1\n            -showUnitlessCurves 1\n            -showCompounds 1\n            -showLeafs 1\n            -showNumericAttrsOnly 0\n            -highlightActive 1\n            -autoSelectNewObjects 0\n            -doNotSelectNewObjects 0\n            -dropIsParent 1\n            -transmitFilters 0\n            -setFilter \"defaultSetFilter\" \n            -showSetMembers 1\n            -allowMultiSelection 1\n            -alwaysToggleSelect 0\n            -directSelect 0\n            -displayMode \"DAG\" \n            -expandObjects 0\n"
		+ "            -setsIgnoreFilters 1\n            -containersIgnoreFilters 0\n            -editAttrName 0\n            -showAttrValues 0\n            -highlightSecondary 0\n            -showUVAttrsOnly 0\n            -showTextureNodesOnly 0\n            -attrAlphaOrder \"default\" \n            -animLayerFilterOptions \"allAffecting\" \n            -sortOrder \"none\" \n            -longNames 0\n            -niceNames 1\n            -showNamespace 1\n            -showPinIcons 0\n            -mapMotionTrails 0\n            -ignoreHiddenAttribute 0\n            -ignoreOutlinerColor 0\n            -renderFilterVisible 0\n            $editorName;\n\t\tif (!$useSceneConfig) {\n\t\t\tpanel -e -l $label $panelName;\n\t\t}\n\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextScriptedPanel \"graphEditor\" (localizedPanelLabel(\"Graph Editor\")) `;\n\tif (\"\" != $panelName) {\n\t\t$label = `panel -q -label $panelName`;\n\t\tscriptedPanel -edit -l (localizedPanelLabel(\"Graph Editor\")) -mbv $menusOkayInPanels  $panelName;\n\n\t\t\t$editorName = ($panelName+\"OutlineEd\");\n            outlinerEditor -e \n"
		+ "                -showShapes 1\n                -showAssignedMaterials 0\n                -showTimeEditor 1\n                -showReferenceNodes 0\n                -showReferenceMembers 0\n                -showAttributes 1\n                -showConnected 1\n                -showAnimCurvesOnly 1\n                -showMuteInfo 0\n                -organizeByLayer 1\n                -organizeByClip 1\n                -showAnimLayerWeight 1\n                -autoExpandLayers 1\n                -autoExpand 1\n                -showDagOnly 0\n                -showAssets 1\n                -showContainedOnly 0\n                -showPublishedAsConnected 0\n                -showParentContainers 0\n                -showContainerContents 0\n                -ignoreDagHierarchy 0\n                -expandConnections 1\n                -showUpstreamCurves 1\n                -showUnitlessCurves 1\n                -showCompounds 0\n                -showLeafs 1\n                -showNumericAttrsOnly 1\n                -highlightActive 0\n                -autoSelectNewObjects 1\n"
		+ "                -doNotSelectNewObjects 0\n                -dropIsParent 1\n                -transmitFilters 1\n                -setFilter \"0\" \n                -showSetMembers 0\n                -allowMultiSelection 1\n                -alwaysToggleSelect 0\n                -directSelect 0\n                -displayMode \"DAG\" \n                -expandObjects 0\n                -setsIgnoreFilters 1\n                -containersIgnoreFilters 0\n                -editAttrName 0\n                -showAttrValues 0\n                -highlightSecondary 0\n                -showUVAttrsOnly 0\n                -showTextureNodesOnly 0\n                -attrAlphaOrder \"default\" \n                -animLayerFilterOptions \"allAffecting\" \n                -sortOrder \"none\" \n                -longNames 0\n                -niceNames 1\n                -showNamespace 1\n                -showPinIcons 1\n                -mapMotionTrails 1\n                -ignoreHiddenAttribute 0\n                -ignoreOutlinerColor 0\n                -renderFilterVisible 0\n                $editorName;\n"
		+ "\n\t\t\t$editorName = ($panelName+\"GraphEd\");\n            animCurveEditor -e \n                -displayValues 0\n                -snapTime \"integer\" \n                -snapValue \"none\" \n                -showPlayRangeShades \"on\" \n                -lockPlayRangeShades \"off\" \n                -smoothness \"fine\" \n                -resultSamples 1\n                -resultScreenSamples 0\n                -resultUpdate \"delayed\" \n                -showUpstreamCurves 1\n                -keyMinScale 1\n                -stackedCurvesMin -1\n                -stackedCurvesMax 1\n                -stackedCurvesSpace 0.2\n                -preSelectionHighlight 0\n                -constrainDrag 0\n                -valueLinesToggle 1\n                -outliner \"graphEditor1OutlineEd\" \n                -highlightAffectedCurves 0\n                $editorName;\n\t\tif (!$useSceneConfig) {\n\t\t\tpanel -e -l $label $panelName;\n\t\t}\n\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextScriptedPanel \"dopeSheetPanel\" (localizedPanelLabel(\"Dope Sheet\")) `;\n\tif (\"\" != $panelName) {\n"
		+ "\t\t$label = `panel -q -label $panelName`;\n\t\tscriptedPanel -edit -l (localizedPanelLabel(\"Dope Sheet\")) -mbv $menusOkayInPanels  $panelName;\n\n\t\t\t$editorName = ($panelName+\"OutlineEd\");\n            outlinerEditor -e \n                -showShapes 1\n                -showAssignedMaterials 0\n                -showTimeEditor 1\n                -showReferenceNodes 0\n                -showReferenceMembers 0\n                -showAttributes 1\n                -showConnected 1\n                -showAnimCurvesOnly 1\n                -showMuteInfo 0\n                -organizeByLayer 1\n                -organizeByClip 1\n                -showAnimLayerWeight 1\n                -autoExpandLayers 1\n                -autoExpand 0\n                -showDagOnly 0\n                -showAssets 1\n                -showContainedOnly 0\n                -showPublishedAsConnected 0\n                -showParentContainers 0\n                -showContainerContents 0\n                -ignoreDagHierarchy 0\n                -expandConnections 1\n                -showUpstreamCurves 1\n"
		+ "                -showUnitlessCurves 0\n                -showCompounds 1\n                -showLeafs 1\n                -showNumericAttrsOnly 1\n                -highlightActive 0\n                -autoSelectNewObjects 0\n                -doNotSelectNewObjects 1\n                -dropIsParent 1\n                -transmitFilters 0\n                -setFilter \"0\" \n                -showSetMembers 0\n                -allowMultiSelection 1\n                -alwaysToggleSelect 0\n                -directSelect 0\n                -displayMode \"DAG\" \n                -expandObjects 0\n                -setsIgnoreFilters 1\n                -containersIgnoreFilters 0\n                -editAttrName 0\n                -showAttrValues 0\n                -highlightSecondary 0\n                -showUVAttrsOnly 0\n                -showTextureNodesOnly 0\n                -attrAlphaOrder \"default\" \n                -animLayerFilterOptions \"allAffecting\" \n                -sortOrder \"none\" \n                -longNames 0\n                -niceNames 1\n                -showNamespace 1\n"
		+ "                -showPinIcons 0\n                -mapMotionTrails 1\n                -ignoreHiddenAttribute 0\n                -ignoreOutlinerColor 0\n                -renderFilterVisible 0\n                $editorName;\n\n\t\t\t$editorName = ($panelName+\"DopeSheetEd\");\n            dopeSheetEditor -e \n                -displayValues 0\n                -snapTime \"integer\" \n                -snapValue \"none\" \n                -outliner \"dopeSheetPanel1OutlineEd\" \n                -showSummary 1\n                -showScene 0\n                -hierarchyBelow 0\n                -showTicks 1\n                -selectionWindow 0 0 0 0 \n                $editorName;\n\t\tif (!$useSceneConfig) {\n\t\t\tpanel -e -l $label $panelName;\n\t\t}\n\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextScriptedPanel \"timeEditorPanel\" (localizedPanelLabel(\"Time Editor\")) `;\n\tif (\"\" != $panelName) {\n\t\t$label = `panel -q -label $panelName`;\n\t\tscriptedPanel -edit -l (localizedPanelLabel(\"Time Editor\")) -mbv $menusOkayInPanels  $panelName;\n\t\tif (!$useSceneConfig) {\n\t\t\tpanel -e -l $label $panelName;\n"
		+ "\t\t}\n\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextScriptedPanel \"clipEditorPanel\" (localizedPanelLabel(\"Trax Editor\")) `;\n\tif (\"\" != $panelName) {\n\t\t$label = `panel -q -label $panelName`;\n\t\tscriptedPanel -edit -l (localizedPanelLabel(\"Trax Editor\")) -mbv $menusOkayInPanels  $panelName;\n\n\t\t\t$editorName = clipEditorNameFromPanel($panelName);\n            clipEditor -e \n                -displayValues 0\n                -snapTime \"none\" \n                -snapValue \"none\" \n                -initialized 0\n                -manageSequencer 0 \n                $editorName;\n\t\tif (!$useSceneConfig) {\n\t\t\tpanel -e -l $label $panelName;\n\t\t}\n\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextScriptedPanel \"sequenceEditorPanel\" (localizedPanelLabel(\"Camera Sequencer\")) `;\n\tif (\"\" != $panelName) {\n\t\t$label = `panel -q -label $panelName`;\n\t\tscriptedPanel -edit -l (localizedPanelLabel(\"Camera Sequencer\")) -mbv $menusOkayInPanels  $panelName;\n\n\t\t\t$editorName = sequenceEditorNameFromPanel($panelName);\n            clipEditor -e \n                -displayValues 0\n"
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
		+ "                -displayMode \"centerEye\" \n                -viewColor 0 0 0 1 \n                -useCustomBackground 1\n                $editorName;\n            stereoCameraView -e -viewSelected 0 $editorName;\n            stereoCameraView -e \n                -pluginObjects \"gpuCacheDisplayFilter\" 1 \n                $editorName; };\n\t\tif (!$useSceneConfig) {\n\t\t\tpanel -e -l $label $panelName;\n\t\t}\n\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextPanel \"outlinerPanel\" (localizedPanelLabel(\"ToggledOutliner\")) `;\n\tif (\"\" != $panelName) {\n\t\t$label = `panel -q -label $panelName`;\n\t\toutlinerPanel -edit -l (localizedPanelLabel(\"ToggledOutliner\")) -mbv $menusOkayInPanels  $panelName;\n\t\t$editorName = $panelName;\n        outlinerEditor -e \n            -docTag \"isolOutln_fromSeln\" \n            -showShapes 0\n            -showAssignedMaterials 0\n            -showTimeEditor 1\n            -showReferenceNodes 1\n            -showReferenceMembers 1\n            -showAttributes 0\n            -showConnected 0\n            -showAnimCurvesOnly 0\n"
		+ "            -showMuteInfo 0\n            -organizeByLayer 1\n            -organizeByClip 1\n            -showAnimLayerWeight 1\n            -autoExpandLayers 1\n            -autoExpand 0\n            -showDagOnly 1\n            -showAssets 1\n            -showContainedOnly 1\n            -showPublishedAsConnected 0\n            -showParentContainers 0\n            -showContainerContents 1\n            -ignoreDagHierarchy 0\n            -expandConnections 0\n            -showUpstreamCurves 1\n            -showUnitlessCurves 1\n            -showCompounds 1\n            -showLeafs 1\n            -showNumericAttrsOnly 0\n            -highlightActive 1\n            -autoSelectNewObjects 0\n            -doNotSelectNewObjects 0\n            -dropIsParent 1\n            -transmitFilters 0\n            -setFilter \"defaultSetFilter\" \n            -showSetMembers 1\n            -allowMultiSelection 1\n            -alwaysToggleSelect 0\n            -directSelect 0\n            -isSet 0\n            -isSetMember 0\n            -displayMode \"DAG\" \n            -expandObjects 0\n"
		+ "            -setsIgnoreFilters 1\n            -containersIgnoreFilters 0\n            -editAttrName 0\n            -showAttrValues 0\n            -highlightSecondary 0\n            -showUVAttrsOnly 0\n            -showTextureNodesOnly 0\n            -attrAlphaOrder \"default\" \n            -animLayerFilterOptions \"allAffecting\" \n            -sortOrder \"none\" \n            -longNames 0\n            -niceNames 1\n            -selectCommand \"print(\\\"\\\")\" \n            -showNamespace 1\n            -showPinIcons 0\n            -mapMotionTrails 0\n            -ignoreHiddenAttribute 0\n            -ignoreOutlinerColor 0\n            -renderFilterVisible 0\n            -renderFilterIndex 0\n            -selectionOrder \"chronological\" \n            -expandAttribute 0\n            $editorName;\n\t\tif (!$useSceneConfig) {\n\t\t\tpanel -e -l $label $panelName;\n\t\t}\n\t}\n\n\n\tif ($useSceneConfig) {\n        string $configName = `getPanel -cwl (localizedPanelLabel(\"Current Layout\"))`;\n        if (\"\" != $configName) {\n\t\t\tpanelConfiguration -edit -label (localizedPanelLabel(\"Current Layout\")) \n"
		+ "\t\t\t\t-userCreated false\n\t\t\t\t-defaultImage \"vacantCell.xP:/\"\n\t\t\t\t-image \"\"\n\t\t\t\t-sc false\n\t\t\t\t-configString \"global string $gMainPane; paneLayout -e -cn \\\"single\\\" -ps 1 100 100 $gMainPane;\"\n\t\t\t\t-removeAllPanels\n\t\t\t\t-ap false\n\t\t\t\t\t(localizedPanelLabel(\"Persp View\")) \n\t\t\t\t\t\"modelPanel\"\n"
		+ "\t\t\t\t\t\"$panelName = `modelPanel -unParent -l (localizedPanelLabel(\\\"Persp View\\\")) -mbv $menusOkayInPanels `;\\n$editorName = $panelName;\\nmodelEditor -e \\n    -docTag \\\"RADRENDER\\\" \\n    -editorChanged \\\"updateModelPanelBar\\\" \\n    -cam `findStartUpCamera persp` \\n    -useInteractiveMode 0\\n    -displayLights \\\"default\\\" \\n    -displayAppearance \\\"smoothShaded\\\" \\n    -activeOnly 0\\n    -ignorePanZoom 0\\n    -wireframeOnShaded 0\\n    -headsUpDisplay 1\\n    -holdOuts 1\\n    -selectionHiliteDisplay 1\\n    -useDefaultMaterial 0\\n    -bufferMode \\\"double\\\" \\n    -twoSidedLighting 0\\n    -backfaceCulling 0\\n    -xray 0\\n    -jointXray 0\\n    -activeComponentsXray 0\\n    -displayTextures 0\\n    -smoothWireframe 0\\n    -lineWidth 1\\n    -textureAnisotropic 0\\n    -textureHilight 1\\n    -textureSampling 2\\n    -textureDisplay \\\"modulate\\\" \\n    -textureMaxSize 16384\\n    -fogging 0\\n    -fogSource \\\"fragment\\\" \\n    -fogMode \\\"linear\\\" \\n    -fogStart 0\\n    -fogEnd 100\\n    -fogDensity 0.1\\n    -fogColor 0.5 0.5 0.5 1 \\n    -depthOfFieldPreview 1\\n    -maxConstantTransparency 1\\n    -rendererName \\\"vp2Renderer\\\" \\n    -objectFilterShowInHUD 1\\n    -isFiltered 0\\n    -colorResolution 256 256 \\n    -bumpResolution 512 512 \\n    -textureCompression 0\\n    -transparencyAlgorithm \\\"frontAndBackCull\\\" \\n    -transpInShadows 0\\n    -cullingOverride \\\"none\\\" \\n    -lowQualityLighting 0\\n    -maximumNumHardwareLights 1\\n    -occlusionCulling 0\\n    -shadingModel 0\\n    -useBaseRenderer 0\\n    -useReducedRenderer 0\\n    -smallObjectCulling 0\\n    -smallObjectThreshold -1 \\n    -interactiveDisableShadows 0\\n    -interactiveBackFaceCull 0\\n    -sortTransparent 1\\n    -controllers 1\\n    -nurbsCurves 1\\n    -nurbsSurfaces 1\\n    -polymeshes 1\\n    -subdivSurfaces 1\\n    -planes 1\\n    -lights 1\\n    -cameras 1\\n    -controlVertices 1\\n    -hulls 1\\n    -grid 1\\n    -imagePlane 1\\n    -joints 1\\n    -ikHandles 1\\n    -deformers 1\\n    -dynamics 1\\n    -particleInstancers 1\\n    -fluids 1\\n    -hairSystems 1\\n    -follicles 1\\n    -nCloths 1\\n    -nParticles 1\\n    -nRigids 1\\n    -dynamicConstraints 1\\n    -locators 1\\n    -manipulators 1\\n    -pluginShapes 1\\n    -dimensions 1\\n    -handles 1\\n    -pivots 1\\n    -textures 1\\n    -strokes 1\\n    -motionTrails 1\\n    -clipGhosts 1\\n    -greasePencils 1\\n    -shadows 0\\n    -captureSequenceNumber -1\\n    -width 1180\\n    -height 928\\n    -sceneRenderFilter 0\\n    -activeShadingGraph \\\"ballora_animatronic_shadow_rig:rsMaterial1SG,ballora_animatronic_shadow_rig:MAT_ballora,ballora_animatronic_shadow_rig:MAT_ballora\\\" \\n    -activeCustomGeometry \\\"meshShaderball\\\" \\n    $editorName;\\nmodelEditor -e -viewSelected 0 $editorName;\\nmodelEditor -e \\n    -pluginObjects \\\"gpuCacheDisplayFilter\\\" 1 \\n    $editorName\"\n"
		+ "\t\t\t\t\t\"modelPanel -edit -l (localizedPanelLabel(\\\"Persp View\\\")) -mbv $menusOkayInPanels  $panelName;\\n$editorName = $panelName;\\nmodelEditor -e \\n    -docTag \\\"RADRENDER\\\" \\n    -editorChanged \\\"updateModelPanelBar\\\" \\n    -cam `findStartUpCamera persp` \\n    -useInteractiveMode 0\\n    -displayLights \\\"default\\\" \\n    -displayAppearance \\\"smoothShaded\\\" \\n    -activeOnly 0\\n    -ignorePanZoom 0\\n    -wireframeOnShaded 0\\n    -headsUpDisplay 1\\n    -holdOuts 1\\n    -selectionHiliteDisplay 1\\n    -useDefaultMaterial 0\\n    -bufferMode \\\"double\\\" \\n    -twoSidedLighting 0\\n    -backfaceCulling 0\\n    -xray 0\\n    -jointXray 0\\n    -activeComponentsXray 0\\n    -displayTextures 0\\n    -smoothWireframe 0\\n    -lineWidth 1\\n    -textureAnisotropic 0\\n    -textureHilight 1\\n    -textureSampling 2\\n    -textureDisplay \\\"modulate\\\" \\n    -textureMaxSize 16384\\n    -fogging 0\\n    -fogSource \\\"fragment\\\" \\n    -fogMode \\\"linear\\\" \\n    -fogStart 0\\n    -fogEnd 100\\n    -fogDensity 0.1\\n    -fogColor 0.5 0.5 0.5 1 \\n    -depthOfFieldPreview 1\\n    -maxConstantTransparency 1\\n    -rendererName \\\"vp2Renderer\\\" \\n    -objectFilterShowInHUD 1\\n    -isFiltered 0\\n    -colorResolution 256 256 \\n    -bumpResolution 512 512 \\n    -textureCompression 0\\n    -transparencyAlgorithm \\\"frontAndBackCull\\\" \\n    -transpInShadows 0\\n    -cullingOverride \\\"none\\\" \\n    -lowQualityLighting 0\\n    -maximumNumHardwareLights 1\\n    -occlusionCulling 0\\n    -shadingModel 0\\n    -useBaseRenderer 0\\n    -useReducedRenderer 0\\n    -smallObjectCulling 0\\n    -smallObjectThreshold -1 \\n    -interactiveDisableShadows 0\\n    -interactiveBackFaceCull 0\\n    -sortTransparent 1\\n    -controllers 1\\n    -nurbsCurves 1\\n    -nurbsSurfaces 1\\n    -polymeshes 1\\n    -subdivSurfaces 1\\n    -planes 1\\n    -lights 1\\n    -cameras 1\\n    -controlVertices 1\\n    -hulls 1\\n    -grid 1\\n    -imagePlane 1\\n    -joints 1\\n    -ikHandles 1\\n    -deformers 1\\n    -dynamics 1\\n    -particleInstancers 1\\n    -fluids 1\\n    -hairSystems 1\\n    -follicles 1\\n    -nCloths 1\\n    -nParticles 1\\n    -nRigids 1\\n    -dynamicConstraints 1\\n    -locators 1\\n    -manipulators 1\\n    -pluginShapes 1\\n    -dimensions 1\\n    -handles 1\\n    -pivots 1\\n    -textures 1\\n    -strokes 1\\n    -motionTrails 1\\n    -clipGhosts 1\\n    -greasePencils 1\\n    -shadows 0\\n    -captureSequenceNumber -1\\n    -width 1180\\n    -height 928\\n    -sceneRenderFilter 0\\n    -activeShadingGraph \\\"ballora_animatronic_shadow_rig:rsMaterial1SG,ballora_animatronic_shadow_rig:MAT_ballora,ballora_animatronic_shadow_rig:MAT_ballora\\\" \\n    -activeCustomGeometry \\\"meshShaderball\\\" \\n    $editorName;\\nmodelEditor -e -viewSelected 0 $editorName;\\nmodelEditor -e \\n    -pluginObjects \\\"gpuCacheDisplayFilter\\\" 1 \\n    $editorName\"\n"
		+ "\t\t\t\t$configName;\n\n            setNamedPanelLayout (localizedPanelLabel(\"Current Layout\"));\n        }\n\n        panelHistory -e -clear mainPanelHistory;\n        sceneUIReplacement -clear;\n\t}\n\n\ngrid -spacing 5 -size 12 -divisions 5 -displayAxes yes -displayGridLines yes -displayDivisionLines yes -displayPerspectiveLabels no -displayOrthographicLabels no -displayAxesBold yes -perspectiveLabelPosition axis -orthographicLabelPosition edge;\nviewManip -drawCompass 0 -compassAngle 0 -frontParameters \"\" -homeParameters \"\" -selectionLockParameters \"\";\n}\n");
	setAttr ".st" 3;
createNode script -n "sceneConfigurationScriptNode";
	rename -uid "BC82FABA-4136-896F-0663-6C9A38D2E0CC";
	setAttr ".b" -type "string" "playbackOptions -min 1 -max 120 -ast 1 -aet 200 ";
	setAttr ".st" 6;
createNode network -n "LFT_fingers";
	rename -uid "462CAC0B-424C-B6D0-A0C2-1AA354BCBBEB";
	addAttr -ci true -k true -sn "name" -ln "name" -dt "string";
	addAttr -ci true -k true -sn "enable" -ln "enable" -min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "isBuild" -ln "isBuild" -min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "class" -ln "class" -dt "string";
	addAttr -ci true -k true -sn "parent" -ln "parent" -dt "string";
	addAttr -ci true -k true -sn "control_scale" -ln "control_scale" -min 0 -max 1 -at "float";
	addAttr -ci true -k true -sn "debug_mode" -ln "debug_mode" -min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "mirror_control_scale" -ln "mirror_control_scale" -min 
		0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "pole_distance" -ln "pole_distance" -dv 3 -at "float";
	addAttr -ci true -k true -sn "list_finger_base_joints" -ln "list_finger_base_joints" 
		-dt "stringArray";
	addAttr -ci true -k true -sn "list_finger_start_joints" -ln "list_finger_start_joints" 
		-dt "stringArray";
	addAttr -ci true -k true -sn "enable_thumb" -ln "enable_thumb" -min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "thumb_base_joint" -ln "thumb_base_joint" -dt "string";
	addAttr -ci true -k true -sn "thumb_start_joint" -ln "thumb_start_joint" -dt "string";
	addAttr -ci true -k true -sn "enable_ik_hand_support" -ln "enable_ik_hand_support" 
		-min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "jnt_ik_middle" -ln "jnt_ik_middle" -dt "string";
	addAttr -ci true -k true -sn "enable_cup_control" -ln "enable_cup_control" -min 
		0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "cup_control_pivot" -ln "cup_control_pivot" -dt "string";
	addAttr -ci true -k true -sn "list_finger_keyword" -ln "list_finger_keyword" -dt "stringArray";
	addAttr -ci true -k true -sn "thumb_keyword" -ln "thumb_keyword" -dt "string";
	addAttr -ci true -k true -sn "axis_pole_finger" -ln "axis_pole_finger" -min 0 -max 
		5 -en "X:Y:Z:-X:-Y:-Z" -at "enum";
	addAttr -ci true -k true -sn "filter_finger_by_keyword" -ln "filter_finger_by_keyword" 
		-min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "filter_thumb_by_keyword" -ln "filter_thumb_by_keyword" 
		-min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "enable_finger_base" -ln "enable_finger_base" -min 
		0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "enable_thumb_base" -ln "enable_thumb_base" -min 0 
		-max 1 -at "bool";
	setAttr -k on ".name" -type "string" "LFT_fingers";
	setAttr -k on ".enable" yes;
	setAttr -k on ".class" -type "string" "EasySkeleton.rigs.BodyGlobal.Fingers";
	setAttr -k on ".parent" -type "string" "LFT_hand";
	setAttr -k on ".control_scale" 0.40000000596046448;
	setAttr -k on ".pole_distance" -3;
	setAttr -k on ".list_finger_base_joints" -type "stringArray" 4 "LFT_index1" "LFT_middle1" "LFT_ring1" "LFT_pinky1"  ;
	setAttr -k on ".list_finger_start_joints" -type "stringArray" 4 "LFT_index2" "LFT_middle2" "LFT_ring2" "LFT_pinky2"  ;
	setAttr -k on ".enable_thumb" yes;
	setAttr -k on ".thumb_base_joint" -type "string" "LFT_thumb1";
	setAttr -k on ".thumb_start_joint" -type "string" "LFT_thumb2";
	setAttr -k on ".jnt_ik_middle" -type "string" "";
	setAttr -k on ".cup_control_pivot" -type "string" "";
	setAttr -k on ".list_finger_keyword" -type "stringArray" 4 "index" "middle" "ring" "pinky"  ;
	setAttr -k on ".thumb_keyword" -type "string" "thumb";
	setAttr -k on ".axis_pole_finger" 2;
	setAttr -k on ".enable_finger_base" yes;
	setAttr -k on ".enable_thumb_base" yes;
createNode network -n "RGT_fingers";
	rename -uid "ADD4CEC6-4431-DF80-D51F-ADB3536E42C5";
	addAttr -ci true -k true -sn "name" -ln "name" -dt "string";
	addAttr -ci true -k true -sn "enable" -ln "enable" -min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "isBuild" -ln "isBuild" -min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "class" -ln "class" -dt "string";
	addAttr -ci true -k true -sn "parent" -ln "parent" -dt "string";
	addAttr -ci true -k true -sn "control_scale" -ln "control_scale" -min 0 -max 1 -at "float";
	addAttr -ci true -k true -sn "debug_mode" -ln "debug_mode" -min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "mirror_control_scale" -ln "mirror_control_scale" -min 
		0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "pole_distance" -ln "pole_distance" -dv 3 -at "float";
	addAttr -ci true -k true -sn "list_finger_base_joints" -ln "list_finger_base_joints" 
		-dt "stringArray";
	addAttr -ci true -k true -sn "list_finger_start_joints" -ln "list_finger_start_joints" 
		-dt "stringArray";
	addAttr -ci true -k true -sn "enable_thumb" -ln "enable_thumb" -min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "thumb_base_joint" -ln "thumb_base_joint" -dt "string";
	addAttr -ci true -k true -sn "thumb_start_joint" -ln "thumb_start_joint" -dt "string";
	addAttr -ci true -k true -sn "enable_ik_hand_support" -ln "enable_ik_hand_support" 
		-min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "jnt_ik_middle" -ln "jnt_ik_middle" -dt "string";
	addAttr -ci true -k true -sn "enable_cup_control" -ln "enable_cup_control" -min 
		0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "cup_control_pivot" -ln "cup_control_pivot" -dt "string";
	addAttr -ci true -k true -sn "list_finger_keyword" -ln "list_finger_keyword" -dt "stringArray";
	addAttr -ci true -k true -sn "thumb_keyword" -ln "thumb_keyword" -dt "string";
	addAttr -ci true -k true -sn "axis_pole_finger" -ln "axis_pole_finger" -min 0 -max 
		5 -en "X:Y:Z:-X:-Y:-Z" -at "enum";
	addAttr -ci true -k true -sn "filter_finger_by_keyword" -ln "filter_finger_by_keyword" 
		-min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "filter_thumb_by_keyword" -ln "filter_thumb_by_keyword" 
		-min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "enable_finger_base" -ln "enable_finger_base" -min 
		0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "enable_thumb_base" -ln "enable_thumb_base" -min 0 
		-max 1 -at "bool";
	setAttr -k on ".name" -type "string" "RGT_fingers";
	setAttr -k on ".enable" yes;
	setAttr -k on ".class" -type "string" "EasySkeleton.rigs.BodyGlobal.Fingers";
	setAttr -k on ".parent" -type "string" "RGT_hand";
	setAttr -k on ".control_scale" 0.40000000596046448;
	setAttr -k on ".mirror_control_scale" yes;
	setAttr -k on ".list_finger_base_joints" -type "stringArray" 4 "RGT_index1" "RGT_middle1" "RGT_ring1" "RGT_pinky1"  ;
	setAttr -k on ".list_finger_start_joints" -type "stringArray" 4 "RGT_index2" "RGT_middle2" "RGT_ring2" "RGT_pinky2"  ;
	setAttr -k on ".enable_thumb" yes;
	setAttr -k on ".thumb_base_joint" -type "string" "RGT_thumb1";
	setAttr -k on ".thumb_start_joint" -type "string" "RGT_thumb2";
	setAttr -k on ".jnt_ik_middle" -type "string" "";
	setAttr -k on ".cup_control_pivot" -type "string" "";
	setAttr -k on ".list_finger_keyword" -type "stringArray" 4 "index" "middle" "ring" "pinky"  ;
	setAttr -k on ".thumb_keyword" -type "string" "thumb";
	setAttr -k on ".axis_pole_finger" 2;
	setAttr -k on ".enable_finger_base" yes;
	setAttr -k on ".enable_thumb_base" yes;
createNode nodeGraphEditorInfo -n "MayaNodeEditorSavedTabsInfo";
	rename -uid "4DC9E5FD-4F96-1DA4-96CC-54BAA100627F";
	setAttr ".tgi[0].tn" -type "string" "Untitled_1";
	setAttr ".tgi[0].vl" -type "double2" -213.62489119358187 -433.87426899784197 ;
	setAttr ".tgi[0].vh" -type "double2" 1063.9209381411949 434.85689494980636 ;
	setAttr -s 2 ".tgi[0].ni";
	setAttr ".tgi[0].ni[0].x" 178.57142639160156;
	setAttr ".tgi[0].ni[0].y" 150;
	setAttr ".tgi[0].ni[0].nvs" 18306;
	setAttr ".tgi[0].ni[1].x" -128.57142639160156;
	setAttr ".tgi[0].ni[1].y" 381.42855834960938;
	setAttr ".tgi[0].ni[1].nvs" 18306;
createNode volumeFog -n "sphereFog";
	rename -uid "49B715C8-41C9-EB8B-2C21-27887E6213CB";
	setAttr -s 4 ".crm";
	setAttr ".crm[0].crmp" 0;
	setAttr ".crm[0].crmc" -type "float3" 1 0 0 ;
	setAttr ".crm[0].crmi" 1;
	setAttr ".crm[1].crmp" 0.33000001311302185;
	setAttr ".crm[1].crmc" -type "float3" 1 1 0 ;
	setAttr ".crm[1].crmi" 1;
	setAttr ".crm[2].crmp" 0.6600000262260437;
	setAttr ".crm[2].crmc" -type "float3" 0 1 0 ;
	setAttr ".crm[2].crmi" 1;
	setAttr ".crm[3].crmp" 1;
	setAttr ".crm[3].crmc" -type "float3" 0 0 1 ;
	setAttr ".crm[3].crmi" 1;
	setAttr ".dos" 1;
createNode shadingEngine -n "sphereFogSG";
	rename -uid "3755EA39-4923-8BFB-45D7-CDB361C6124A";
	setAttr ".ihi" 0;
	setAttr ".ro" yes;
createNode materialInfo -n "materialInfo1";
	rename -uid "D4BF382B-4BCD-39CA-26B8-F48C22B009A5";
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
	setAttr -s 3 ".st";
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
	setAttr -s 6 ".s";
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
	setAttr -k on ".ai_surface_shader";
	setAttr -cb on ".ai_surface_shaderr";
	setAttr -cb on ".ai_surface_shaderg";
	setAttr -cb on ".ai_surface_shaderb";
	setAttr -k on ".ai_volume_shader";
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
	setAttr -k on ".ai_surface_shader";
	setAttr -cb on ".ai_surface_shaderr";
	setAttr -cb on ".ai_surface_shaderg";
	setAttr -cb on ".ai_surface_shaderb";
	setAttr -k on ".ai_volume_shader";
	setAttr -cb on ".ai_volume_shaderr";
	setAttr -cb on ".ai_volume_shaderg";
	setAttr -cb on ".ai_volume_shaderb";
select -ne :defaultRenderGlobals;
	addAttr -ci true -h true -sn "dss" -ln "defaultSurfaceShader" -dt "string";
	setAttr -av -k on ".cch";
	setAttr -cb on ".ihi";
	setAttr -av -k on ".nds";
	setAttr -cb on ".bnm";
	setAttr -av -cb on ".macc";
	setAttr -av -cb on ".macd";
	setAttr -av -cb on ".macq";
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
	setAttr -av -cb on ".sosl";
	setAttr -av -k on ".rd";
	setAttr -av -k on ".lp";
	setAttr -av -k on ".sp";
	setAttr -av -k on ".shs";
	setAttr -av -k on ".lpr";
	setAttr -cb on ".gv";
	setAttr -cb on ".sv";
	setAttr -av -k on ".mm";
	setAttr -av -k on ".npu";
	setAttr -av -cb on ".itf";
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
	setAttr -av -cb on ".jfc";
	setAttr -cb on ".rsb";
	setAttr -av -cb on ".ope";
	setAttr -av -cb on ".oppf";
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
	setAttr -av -k on ".hwcc";
	setAttr -av -k on ".hwdp";
	setAttr -av -k on ".hwql";
	setAttr -av -k on ".hwfr";
	setAttr -av -k on ".soll";
	setAttr -av -k on ".sosl";
	setAttr -av -k on ".bswa";
	setAttr -av -k on ".shml";
	setAttr -av -k on ".hwel";
connectAttr "rootLoc.wm" "GlobalJoints.opm";
connectAttr "LFT_clavicle.s" "LFT_armUp.is";
connectAttr "LFT_armUp.s" "LFT_armLow.is";
connectAttr "LFT_armLow.s" "LFT_hand.is";
connectAttr "LFT_hand.s" "LFT_palm.is";
connectAttr "LFT_palm.s" "LFT_handTip.is";
connectAttr "LFT_hand.s" "LFT_index1.is";
connectAttr "LFT_index1.s" "LFT_index2.is";
connectAttr "LFT_index2.s" "LFT_index3.is";
connectAttr "LFT_index3.s" "LFT_index4.is";
connectAttr "LFT_index4.s" "LFT_index5.is";
connectAttr "LFT_hand.s" "LFT_middle1.is";
connectAttr "LFT_middle1.s" "LFT_middle2.is";
connectAttr "LFT_middle2.s" "LFT_middle3.is";
connectAttr "LFT_middle3.s" "LFT_middle4.is";
connectAttr "LFT_middle4.s" "LFT_middle5.is";
connectAttr "LFT_hand.s" "LFT_pinky1.is";
connectAttr "LFT_pinky1.s" "LFT_pinky2.is";
connectAttr "LFT_pinky2.s" "LFT_pinky3.is";
connectAttr "LFT_pinky3.s" "LFT_pinky4.is";
connectAttr "LFT_pinky4.s" "LFT_pinky5.is";
connectAttr "LFT_hand.s" "LFT_ring1.is";
connectAttr "LFT_ring1.s" "LFT_ring2.is";
connectAttr "LFT_ring2.s" "LFT_ring3.is";
connectAttr "LFT_ring3.s" "LFT_ring4.is";
connectAttr "LFT_ring4.s" "LFT_ring5.is";
connectAttr "LFT_hand.s" "LFT_thumb1.is";
connectAttr "LFT_thumb1.s" "LFT_thumb2.is";
connectAttr "LFT_thumb2.s" "LFT_thumb3.is";
connectAttr "LFT_thumb3.s" "LFT_thumb4.is";
connectAttr "LFT_legUp.s" "LFT_legLow.is";
connectAttr "LFT_legLow.s" "LFT_ankle.is";
connectAttr "LFT_ankle.s" "LFT_ball.is";
connectAttr "LFT_ball.s" "LFT_toe.is";
connectAttr "LFT_ball.s" "LFT_endFootPiv.is";
connectAttr "LFT_ball.s" "LFT_outerFootPiv.is";
connectAttr "LFT_ball.s" "LFT_innerFootPiv.is";
connectAttr "LFT_ball.s" "LFT_heelFootPiv.is";
connectAttr "neck1.s" "neck2.is";
connectAttr "neck2.s" "head.is";
connectAttr "spine1.s" "spine2.is";
connectAttr "spine2.s" "spine3.is";
connectAttr "spine3.s" "spine4.is";
connectAttr "RGT_clavicle.s" "RGT_armUp.is";
connectAttr "RGT_armUp.s" "RGT_armLow.is";
connectAttr "RGT_armLow.s" "RGT_hand.is";
connectAttr "RGT_hand.s" "RGT_palm.is";
connectAttr "RGT_palm.s" "RGT_handTip.is";
connectAttr "RGT_hand.s" "RGT_index1.is";
connectAttr "RGT_index1.s" "RGT_index2.is";
connectAttr "RGT_index2.s" "RGT_index3.is";
connectAttr "RGT_index3.s" "RGT_index4.is";
connectAttr "RGT_index4.s" "RGT_index5.is";
connectAttr "RGT_hand.s" "RGT_middle1.is";
connectAttr "RGT_middle1.s" "RGT_middle2.is";
connectAttr "RGT_middle2.s" "RGT_middle3.is";
connectAttr "RGT_middle3.s" "RGT_middle4.is";
connectAttr "RGT_middle4.s" "RGT_middle5.is";
connectAttr "RGT_hand.s" "RGT_pinky1.is";
connectAttr "RGT_pinky1.s" "RGT_pinky2.is";
connectAttr "RGT_pinky2.s" "RGT_pinky3.is";
connectAttr "RGT_pinky3.s" "RGT_pinky4.is";
connectAttr "RGT_pinky4.s" "RGT_pinky5.is";
connectAttr "RGT_hand.s" "RGT_ring1.is";
connectAttr "RGT_ring1.s" "RGT_ring2.is";
connectAttr "RGT_ring2.s" "RGT_ring3.is";
connectAttr "RGT_ring3.s" "RGT_ring4.is";
connectAttr "RGT_ring4.s" "RGT_ring5.is";
connectAttr "RGT_hand.s" "RGT_thumb1.is";
connectAttr "RGT_thumb1.s" "RGT_thumb2.is";
connectAttr "RGT_thumb2.s" "RGT_thumb3.is";
connectAttr "RGT_thumb3.s" "RGT_thumb4.is";
connectAttr "RGT_legUp.s" "RGT_legLow.is";
connectAttr "RGT_legLow.s" "RGT_ankle.is";
connectAttr "RGT_ankle.s" "RGT_ball.is";
connectAttr "RGT_ball.s" "RGT_toe.is";
connectAttr "RGT_ball.s" "RGT_endFootPiv.is";
connectAttr "RGT_ball.s" "RGT_outerFootPiv.is";
connectAttr "RGT_ball.s" "RGT_innerFootPiv.is";
connectAttr "RGT_ball.s" "RGT_heelFootPiv.is";
connectAttr "rootLoc.wm" "AutoRig.opm";
relationship "link" ":lightLinker1" ":initialShadingGroup.message" ":defaultLightSet.message";
relationship "link" ":lightLinker1" ":initialParticleSE.message" ":defaultLightSet.message";
relationship "link" ":lightLinker1" "sphereFogSG.message" ":defaultLightSet.message";
relationship "shadowLink" ":lightLinker1" ":initialShadingGroup.message" ":defaultLightSet.message";
relationship "shadowLink" ":lightLinker1" ":initialParticleSE.message" ":defaultLightSet.message";
relationship "shadowLink" ":lightLinker1" "sphereFogSG.message" ":defaultLightSet.message";
connectAttr "layerManager.dli[0]" "defaultLayer.id";
connectAttr "renderLayerManager.rlmi[0]" "defaultRenderLayer.rlid";
connectAttr "LFT_armUp.msg" "MayaNodeEditorSavedTabsInfo.tgi[0].ni[0].dn";
connectAttr "LFT_clavicle.msg" "MayaNodeEditorSavedTabsInfo.tgi[0].ni[1].dn";
connectAttr "sphereFog.oc" "sphereFogSG.vs";
connectAttr "sphereFogSG.msg" "materialInfo1.sg";
connectAttr "sphereFogSG.pa" ":renderPartition.st" -na;
connectAttr "sphereFog.msg" ":defaultShaderList1.s" -na;
connectAttr "defaultRenderLayer.msg" ":defaultRenderingList1.r" -na;
// End of skeleton.ma
