import ManageMiPics
import logging

mmp=ManageMiPics.Manage_Mi_Pics()

print ('start to check year time frame')
for tmp_date_test in ['2012-11-20_','2013-11-20_','2013-11-21_','2013-12-31_','2014-01-31_','2015-02-22_','2016-11-19_','2016-11-20_','2016-11-21_']:
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
for tmp_time_test in ['2013-11-20_00:03:32','2013-12-20_00:03:32','2014-11-20_00:03:32','2014-12-21_00:03:22']:
    print(tmp_time_test)
    print(mmp._check_and_create_destination_folder(tmp_time_test))
