#!/usr/bin/python

# motionElevCorrection.py
# Author: Andrew Kenneth Melkonian
# All rights reserved

import os;
import re;
import subprocess;
import sys;


def motionElevCorrection(grd_path, srtm, ice, rock, resolution, snr_thresh):

	index	= grd_path.rfind("/");
	grd_dir	=".";

	if index > -1:
		grd_dir = grd_path[:index];

	pair  = grd_path[grd_path.rfind("/") + 1 : ];
	pair  = pair[ : re.search("\d{14}_\d{14}",pair).end(0)];
	name  = grd_path[grd_path.rfind("/") + 1 : grd_path.rfind(".")];
	label = name[ : re.search("_[a-zA-Z]+xyz", name).start(0)];

	if os.path.exists(grd_dir + "/"  + name + "_corrected.grd"):
		print("\n***** Corrected grid exists (" + grd_dir + "/"  + name + "_corrected.grd), skipping...\n");
		return;

	print("\nRunning motion-elevation correction on " + grd_path + " ...\n");

	R = "-R" + grd_path;

	snr_grd  = grd_dir + "/" + label + "_snrxyz.grd";
	txt_path = grd_path[ : grd_path.rfind(".grd")] + ".txt";

	if not os.path.exists(snr_grd):
		print("\n***** " + snr_grd + " does not exist, creating from " + txt_path + "...\n");
		cmd = "\ngawk '$0 !~ /a/ {print $1\" \"$2\" \"$4}' " + txt_path + " | xyz2grd -R" + grd_path + " -G" + snr_grd + "\n";
		subprocess.call(cmd,shell=True);

	cmd  = "";
#	cmd  = "\ngrdmask " + ice + " " + R + " -I" + resolution + "= -S5000 -G" + grd_dir + "/test.grd -NNaN/1/1\n";
#	cmd += "\ngrdmask " + ice + " " + R + " -I" + resolution + "= -S" + resolution + " -G" + grd_dir + "/first_pixel.grd -NNaN/1/1\n";
#	cmd += "\ngrdmask " + rock + " " + R + " -I" + resolution + "= -S5000 -G" + grd_dir + "/test2.grd -NNaN/1/1\n";
#	cmd += "\ngrdmask " + rock + " " + R + " -I" + resolution + "= -S" + resolution + " -G" + grd_dir + "/first_pixel2.grd -NNaN/1/1\n";
#	cmd += "\ngrdmask " + ice + " " + R + " -I" + resolution + "= -G" + grd_dir + "/test3.grd -N1/NaN/NaN\n";
#	cmd += "\ngrdmask " + rock + " " + R + " -I" + resolution + "= -G" + grd_dir + "/test4.grd -NNaN/NaN/1\n";
	cmd += "\ngrdmask " + ice + " " + R + " -I" + resolution + "= -G" + grd_dir + "/outside_ice.grd -N1/NaN/NaN\n";
	cmd += "\ngrdmask " + rock + " " + R + " -I" + resolution + "= -G" + grd_dir + "/inside_rock.grd -NNaN/NaN/1\n";
#	cmd += "\ngrdmath " + grd_dir + "/test.grd " + grd_dir + "/test3.grd OR = " + grd_dir + "/bla.grd\n";
#	cmd += "\ngrdmath " + grd_dir + "/bla.grd " + grd_dir + "/first_pixel.grd NAN = " + grd_dir + "/bla.grd\n";
#	cmd += "\ngrdmath " + grd_dir + "/test2.grd " + grd_dir + "/test4.grd OR = " + grd_dir + "/bla2.grd\n";
#	cmd += "\ngrdmath " + grd_dir + "/bla2.grd " + grd_dir + "/first_pixel2.grd NAN = " + grd_dir + "/bla2.grd\n";
#	cmd += "\ngrdmath " + grd_dir + "/bla.grd " + grd_dir + "/bla2.grd AND = " + grd_dir + "/" + name + "_mask.grd\n";
#	cmd += "\ngrdmath " + grd_dir + "/" + name + "_mask.grd " + grd_dir + "/first_pixel.grd NAN = " + grd_dir + "/" + name + "_mask.grd\n";
	cmd += "\ngrdmath " + grd_dir + "/outside_ice.grd " + grd_dir + "/inside_rock.grd AND = " + grd_dir + "/" + name + "_mask.grd\n";
	cmd += "\ngrdmath " + grd_path + " " + grd_dir + "/" + name + "_mask.grd OR = " + grd_dir + "/" + name + "_adj_rock.grd\n";
	cmd += "\ngrdclip " + snr_grd + " -Sb" + snr_thresh + "/NaN -G" + grd_dir + "/temp.grd\n";
	cmd += "\ngrdmath " + grd_dir + "/" + name + "_adj_rock.grd " + grd_dir + "/temp.grd OR = " + grd_dir + "/" + name + "_adj_rock.grd\n";
	subprocess.call(cmd,shell=True);

	os.remove(grd_dir + "/temp.grd");
	os.remove(grd_dir + "/outside_ice.grd");
	os.remove(grd_dir + "/inside_rock.grd");

	cmd  = "\ngrdinfo " + grd_dir + "/" + name + "_mask.grd\n";
	pipe = subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE).stdout;
	info = pipe.read().strip();
	pipe.close();

	x_min = info[re.search("x_min: ",info).end(0):re.search("x_min: \d+\.*\d*",info).end(0)];
	x_max = info[re.search("x_max: ",info).end(0):re.search("x_max: \d+\.*\d*",info).end(0)];
	y_min = info[re.search("y_min: ",info).end(0):re.search("y_min: \d+\.*\d*",info).end(0)];
	y_max = info[re.search("y_max: ",info).end(0):re.search("y_max: \d+\.*\d*",info).end(0)];

	R = "-R" + x_min + "/" + y_min + "/" + x_max + "/" + y_max + "r";

	psname = grd_dir + "/" + name + "_mask.ps";

	cmd  = "makecpt -Crainbow -T-1/1/0.1 > " + grd_dir + "/mask.cpt\n";
	cmd += "\ngrdimage " + grd_dir + "/" + name + "_adj_rock.grd " + R + " -Jx1:400000 -C" + grd_dir + "/mask.cpt -Q -K > " + psname + "\n";
	cmd += "\npsxy " + ice + " -R -J -W0.5p,black -O -K >> " + psname + "\n";
	cmd += "\npsxy " + rock + " -R -J -W0.5p,black -O >> " + psname + "\n";
	subprocess.call(cmd,shell=True);

	cmd  = "\ngrdmath " + grd_path + " " + grd_dir + "/" + name + "_adj_rock.grd OR = " + grd_dir + "/" + name + "_adj.grd\n";
	cmd += "\ngrd2xyz " + grd_dir + "/" + name + "_adj.grd > " + grd_dir + "/" + name + "_adj.txt\n";
	cmd += "\ngrdtrack " + grd_dir + "/" + name + "_adj.txt -nn -G" + srtm + " > " + grd_dir + "/" + name + "_adj_elevs.txt\n";
	subprocess.call(cmd,shell=True);

	cmd  = "\nminmax -C " + grd_dir + "/" + name + "_adj_elevs.txt\n";
	pipe = subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE).stdout;
	info = pipe.read().split();
	pipe.close();

	ymin = info[4];
	ymax = info[5];
	xmin = info[6];
	xmax = info[7];

	cmd  = "gawk '$3 !~ /NaN/ {print $3}' " + grd_dir + "/" + name + "_adj_elevs.txt | gmtmath STDIN MEAN = " + grd_dir + "/mean.dat\n";
	cmd += "gawk '$3 !~ /NaN/ {print $3}' " + grd_dir + "/" + name + "_adj_elevs.txt | gmtmath STDIN STD = " + grd_dir + "/std.dat\n";
	cmd += "gawk '$3 !~ /NaN/ {print $3}' " + grd_dir + "/" + name + "_adj_elevs.txt | gmtmath STDIN MED = " + grd_dir + "/median.dat\n";
	subprocess.call(cmd,shell=True);

	infile	= open(grd_dir + "/mean.dat","r");
	mean	= infile.readline().strip();
	infile.close();

	infile	= open(grd_dir + "/std.dat","r");
	std	= infile.readline().strip();
	infile.close();

	infile	= open(grd_dir + "/median.dat","r");
	median	= infile.readline().strip();
	infile.close();

	os.remove(grd_dir + "/mean.dat");
	os.remove(grd_dir + "/std.dat");
	os.remove(grd_dir + "/median.dat");

	mean_plus_std	= str(float(median)+float(std));
	mean_minus_std	= str(float(median)-float(std));

	cmd   = "\ngawk '$3 !~ /NaN/ && $4 !~ /NaN/ && $3 < " + mean_plus_std + " && $3 > " + mean_minus_std + " {print $4\" \"$3}' " + grd_dir + "/" + name + "_adj_elevs.txt | trend1d -Fm -N2 -V > " + grd_dir + "/bla.txt\n";
	pipe  = subprocess.Popen(cmd,shell=True,stderr=subprocess.PIPE).stderr;
	trend = pipe.read().strip().split("\n");
	pipe.close();

	intercept = "";
	slope	  = "";

	for item in trend:

		if item.find("Polynomial") > -1:
			elements  = item.split();
			intercept = elements[4]
			slope	  = elements[5];

	cmd = "\ngawk '$3 !~ /NaN/ && $4 !~ /NaN/ && $3 < " + mean_plus_std + " && $3 > " + mean_minus_std + " {print $4\" \"$3}' " + grd_dir + "/" + name + "_adj_elevs.txt | psxy -JX5i/5i -R" + xmin + "/" + ymin + "/" + xmax + "/" + ymax + "r -BSa500g500ne/Wa2g2 -Sc0.05c -Gred -K > " + grd_dir + "/" + name + "_adj_elevs_scatter.ps\n";
	cmd +="\necho \"0 " + intercept + "\n2500 " + str(2500.*float(slope)+float(intercept)) + "\" | psxy -J -R -W0.5p,black -O >> " + grd_dir + "/" + name + "_adj_elevs_scatter.ps\n";
	cmd += "\nps2raster -A -Tf " + grd_dir + "/" + name + "_adj_elevs_scatter.ps";
	subprocess.call(cmd,shell=True);

	cmd = "\ngrdtrack " + grd_dir + "/" + name + ".txt -nn -G" + srtm + " > " + grd_dir + "/" + name + "_elevs.txt\n";
	cmd +="\ngawk '$3 !~ /NaN/ && $4 !~ /NaN/ {print $1\" \"$2\" \"$4}' " + grd_dir + "/" + name + "_elevs.txt | xyz2grd -R" + grd_path + " -G" + grd_dir + "/" + name + "_elevs.grd\n";
	cmd +="\ngrdmath " + grd_dir + "/" + name + "_elevs.grd " + slope + " MUL = " + grd_dir + "/" + name + "_elevs.grd\n";
	cmd +="\ngrdmath " + grd_dir + "/" + name + "_elevs.grd " + intercept + " ADD = "  + grd_dir + "/" + name + "_elevs.grd\n";
	cmd +="\ngrdmath " + grd_path + " " + grd_dir + "/" + name + "_elevs.grd SUB --IO_NC4_CHUNK_SIZE=c = " + grd_dir + "/"  + name + "_corrected.grd\n";
	subprocess.call(cmd,shell=True);

	os.remove(grd_dir + "/bla.txt");
 	os.remove(grd_dir + "/" + name + "_elevs.txt");
 	os.remove(grd_dir + "/" + name + "_elevs.grd");
 	os.remove(grd_dir + "/" + name + "_adj_elevs.txt");
 	os.remove(grd_dir + "/" + name + "_adj.txt");
 	os.remove(grd_dir + "/" + name + "_adj.grd");
 	os.remove(grd_dir + "/" + name + "_mask.grd");
 	os.remove(grd_dir + "/" + name + "_mask.ps");
 	os.remove(grd_dir + "/" + name + "_adj_rock.grd");
 	os.remove(grd_dir + "/" + name + "_adj_elevs_scatter.ps");
 	os.remove(grd_dir + "/mask.cpt");

	return;


if __name__ == "__main__":

    import os;
    import sys;

    assert len(sys.argv) > 6, "\n***** ERROR: motionElevCorrection.py requires 6 arguments, " + str(len(sys.argv) - 1) + " given\n";
    assert os.path.exists(sys.argv[1]), "\n***** ERROR: " + sys.argv[1] + " does not exist\n";
    assert os.path.exists(sys.argv[2]), "\n***** ERROR: " + sys.argv[2] + " does not exist\n";
    assert os.path.exists(sys.argv[3]), "\n***** ERROR: " + sys.argv[2] + " does not exist\n";
    assert os.path.exists(sys.argv[4]), "\n***** ERROR: " + sys.argv[2] + " does not exist\n";

    motionElevCorrection(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], sys.argv[6]);

    exit();
