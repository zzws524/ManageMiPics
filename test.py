import ManageMiPics
import logging

mmp=ManageMiPics.Manage_Mi_Pics()
mmp.path_of_folder_to_be_pasted=r'/Users/ziwen/Documents/MyPic/Finsh_bkp'
mmp.path_of_folders_to_be_searched=[r'/Users/ziwen/Documents/MyPic/Finsh']
#mmp._birth_day=1
#mmp._birth_month=1

print ('start to check year time frame')
for tmp_date_test in ['2012-11-20_','2013-11-19_','2013-11-20_','2013-11-21_','2013-12-31_','2014-01-01_','2014-01-31_','2015-02-22_','2016-11-19_','2016-11-20_','2016-11-21_']:
    print(f'{tmp_date_test}:{mmp._define_year_frame_for_subfolder(tmp_date_test)}')

print ('start to check month time frame')
for tmp_date_test in ['2012-11-20_','2013-11-20_','2013-11-21_','2013-12-31_','2014-01-31_','2015-02-22_','2016-11-19_','2016-11-20_','2016-11-21_','2017-12-31_','2018-01-01_']:
    print(f'{tmp_date_test}:{mmp._define_month_frame_for_subfolder(tmp_date_test)}')

print ('start to check diff with birth day')
for tmp_time_test in ['2013-11-20_00:03:32','2013-12-20_00:03:32','2014-11-20_00:03:32','2014-12-21_00:03:22']:
    print(tmp_time_test)
    (diff_year,diff_month)=mmp._get_age_year_month(tmp_time_test)
    print(f'diff_year is {diff_year}')
    print(f'diff_month is {diff_month}')

print ('start to check destination folder')
for tmp_date_test in ['2012-11-20_12:00:01','2013-11-19_12:00:01','2013-11-20_12:00:01','2013-11-21_12:00:01','2013-12-31_12:00:01','2014-01-01_12:00:01','2014-01-31_12:00:01','2015-02-22_12:00:01','2016-11-19_12:00:01','2016-11-20_12:00:01','2016-11-21_12:00:01']:
    print(f'{tmp_date_test}:{mmp._check_and_create_destination_folder(tmp_date_test)}')

print ('start to check get file shot time')
file_names=['20181025_112644_3040.mp4','1544418560235.jpg','IMG_20180726_092712.jpg','mmexport1455977653935.jpg','VID_20160228_124441.mp4','IMG_1004.JPG']
full_path_of_a_file=r'/Users/ziwen/Documents/MyPic/Finish/TestManageMi/null-3fc3e9924e537552.jpg'
for tmp_file in file_names:
    print(f'{tmp_file}: {mmp._get_last_edit_time(tmp_file,full_path_of_a_file)}' )


exif_pics=[r'/Users/ziwen/Documents/MyPic/Finish/TestManageMi/null-3fc3e9924e537552.jpg',r'/Users/ziwen/Documents/MyPic/Finish/TestManageMi/null4e3e9b00d46cb6ac.jpg',r'/Users/ziwen/Documents/MyPic/Finish/TestManageMi/IMG_0005.JPG']
print ('check exif info:')
for exif_pic in exif_pics:
    #print (mmp._get_exif_datetimeoriginal_info(exif_pic))
    print (mmp._get_last_edit_time('fakename',exif_pic))
