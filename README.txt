#############################
#                           #
#    Welcome to ResiRole    #
#                           #
#############################

The set of scripts presented here contain a method for assessing the quality of protein homology models based on the precision with which they reconstitute functional site predictions around specific residues as found in their experimentally determined target structures. These predictions are made on the basis of physiochemical properties as analyzed by the FEATURE program (Halperin, I., et al. The FEATURE framework for protein function annotation: modeling new functions, improving performance, and extending to novel applications. BMC Genomics 2008;9 Suppl 2:S2.), an
algorithm trained to score the residues in any given structure model according to
functional site motifs. ResiRole provides, we believe, an objective measurement of the degree to which physiochemical environments are conserved between any given structure model and its experimentally determined reference structure.

ResiRole is designed to provide information relating to the performance of various structure prediction techniques (modelling servers). Our metrics can rank the general performance of techniques relative to each other as well as provide information regarding techniques' performance on particular structures.

For more information about our methodology and our algorithms, please see the following publication:
    ResiRole: Residue-Level Functional Site Predictions to Gauge the Accuracies of Protein Structure Prediction Techniques. Joshua M. Toth, Paul J. Depietro, Juergen Haas, and William A. McLaughlin. (Publication Under Review).

General Algorithm Overview:
1) FEATURE program is run on both the structure models and corresponding target structures to be analyzed
2) Resulting functional prediction scores are parsed into specificity thresholds based on benchmarking
3) An ROC curve study is performed to determine the optimum cutoff specificity above which to use functional predictions
for subsequent analysis
4) For each technique considered, Difference Score and Correlation Score metrics are calculated and averaged.

About FEATURE:
    FEATURE is an algorithm trained on structures with known functional site motifs annotated by PROSITE (Hulo, N., et al. The PROSITE database. Nucleic acids research 2006;34(suppl_1):D227-D230.) that can score a given structure model for the likeliness it possesses a given functional site based on the physiochemical properties present. FEATURE evaluates these properties by sampling concentric shells of set distances around an anchor residue within the functional site motif. This anchor residue is a highly conserved residue across structures containing the particular type of functional site. Accordingly, any residue of a particular type in a structure model could be scored by FEATURE using all functional site motifs which have that same type of residue as an anchor. For a complete description of the program, please see www.simtk.org/projects/feature. We do not provide the FEATURE program with these scripts. Anyone interested in obtaining its source code can contact the developers. Below are clear directions regarding the directory setup once FEATURE is installed. We choose to utilize the FEATURE program for our purposes due to the breadth of types of functional sites available.

About the ROC curve analysis:
    ResiRole parses the function site prediction Z-scores for structure models and reference structures according to specificity thresholds of 0, 1, 5, 10, 20, 30, 40, 50, 60, 70, 80, 90, 95, 99, and 100 percent based on Z-score the specificity correspondences identified by a previous benchmarking study (Buturovic, L., et al. High precision prediction of functional sites in protein structures. PloS one 2014;9(3):e91240.) and provided courtesy of Mike Wong. A receiver-operator characteristic (ROC) curve analysis is performed in which those predictions in the reference structure that make it to the 100% specificity threshold are considered the "gold standard positives" set. The remaining predictions in the reference structures are considered as negatives. Each model's scores are tallied accordingly, and the resulting ROC curves are analyzed for the benchmarking specificity at which Youden's index is a maximum. All model predictions at or above this specificity threshold are used for subsequent analyses.

About the calculated metrics:
    We define two metrics as the result of the analyses. The Difference Score is calculated as the absolute value of the difference between the functional site prediction probability in a structure model versus the functional site prediction probability at the corresponding site in the experimental structure. A difference score is obtained for each instance of a functional site prediction that is made for each residue of each structure model. An average Difference Score and its standard deviation are calculated for each structure prediction technique by averaging the difference scores for the function site predictions across all the models produced by that structure prediction technique in the given time frame. A Correlation Score is defined as the Pearson's r value associated with a linear regression fit of the plot of all reference structures' functional site prediction probabilities versus all structure models' functional site prediction probabilities for each type of functional site. An average and standard deviation of this metric is then obtained for each structure prediction technique by converting the Pearson r values to Z-scores and averaging across all types of functional sites. The average Pearson r value then reported is the back-converted average Z-score. The Difference Score and Correlation Score are therefore related as follows: the Difference Score for a particular functional site prediction is the absolute value of the difference between the x and y values of a point on a plot of reference structure versus structure model functional site prediction probabilities for that type of function prediction. The Correlation Score is the Pearson r value from a linear regression of that plot.

The scripts and directory structure provided here are designed to provide any user with an example of the ResiRole method. In order to utilize, perform the following steps:

1. Download and unpack the accompanying tar file to the location on your device where you would like to place ResiRole.
2. Specify the path (directory structure) to this location as the 'home' variable located at the top of each script. The scripts could be found in the /ResiRole/scripts/ directory once unpacked. For example, if you unpack the download on your desktop, and the system path to your desktop is '/home/<username>/Desktop/', then the 'home' variable should be set to '/home/<username>/Desktop/ResiRole/' in each script.
3. Ensure you have python installed and operational. Then, specify the python_path variable in each script in which it appears to the location of your python executable.
4. Place your data in the main /ResiRole/ directory and modify the download_home variable if necessary such that your files could be accessed and identified. As an example, this variable is set such as to access 1 week's worth of downloaded data from the CAMEO server (Haas, J., et al. Continuous Automated Model EvaluatiOn (CAMEO) complementing the critical assessment of structure prediction in CASP12. Proteins: Structure, Function, and Bioinformatics 2018;86:387-398.). You could utilize such data for testing by accessing the publicly available download and unpacking it in the /ResiRole/ directory from this link: https://www.cameo3d.org/static/downloads/quality_estimation/1-week/raw_targets-1-week.public.tar.gz. For implementing data of your own, there is no specific format required so long as the pdb id, model name, and files could be identified by the main script. The format of CAMEO data is such that a directory whose name specifies the pdb id and model name contains the model and target .pdb files.
5. Download the FEATURE (www.simtk.org/projects/feature) and dssp (https://swift.cmbi.umcn.nl/gv/dssp/) programs. Place the main dssp executable in the /ResiRole/FEATURE/ directory and place the FEATURE program and all of its contents in
the /ResiRole/FEATURE/feature-3.0.0/ directory. Note that ResiRole currently uses FEATURE version 3.0.0.
6. You may now run ResiRole by executing the main script.

The accompanying study () was performed using approximately four years' worth of data from CAMEO ranging from May 30, 2014 to Feb 24, 2018 (available upon request from CAMEO). Results in this study were obtained utilizing the exact same algorithms in these scripts.

Everything needed to install and work with ResiRole is included in the zip file ResiRole.tar.gz. Alongside we include a folder containing the python scripts through which it is implemented. We encourage users to submit pull requests and offer their contributions to ResiRole through this separate folder. 

Please contact us with any comments, concerns, or requests of additional information:

If you utilize these scripts for your work, please cite the following reference:
    ResiRole: Residue-Level Functional Site Predictions to Gauge the Accuracies of Protein Structure Prediction Techniques. Joshua M. Toth, Paul J. Depietro, Juergen Haas, and William A. McLaughlin. (Publication Under Review).

These scripts are provided under an GNU General Public License v3.0. The ResiRole name is protected by international copyright, trademark, and other laws. You may download and modify these scripts for your personal use provided that you keep intact all authorship, copyright, and other proprietary notices. In addition, please refer to the licensing conditions and policies of CAMEO and FEATURE.

