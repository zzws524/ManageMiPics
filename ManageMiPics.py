"""此文件用于整理米仔的照片到相应的folder。
自动创建folder，格式使用“.../20141120-20151119 (0-1岁合集)/20141120-20141219 （1岁0个月）”
其他照片或视频，以文件的LastModifiedTime 作为标准，将照片转入相应folder内。
有些单反拍摄的文件，时间可能不对。
"""
import os, re, logging, time,shutil
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from typing import List, Callable, Sequence, TypeVar
from PIL import Image
from PIL.ExifTags import TAGS

T = TypeVar('T')

def set_up_logging(level: int) -> None:
    """
    Args:
        level:logging.DEBUG,logging.INFO,etc. Logging level configuration.
    """
    logging.basicConfig(level=level, format='%(asctime)s [line:%(lineno)d] %(levelname)s: %(message)s', datefmt='%d %b %H:%M:%S')
    logger = logging.getLogger(__name__)


class Manage_Mi_Pics:
    """处理照片的类。
    所有数据，被解析到下面这个字典里面：
    master_list={'picture_location':['LastEditTime','OriginalFolderPath','DestinationFolderPath','DuplicateOrUnique','Action']}
    """

    def __init__(self) -> None:
        self.path_of_folders_to_be_searched = []
        self.path_of_folder_to_be_pasted = None
        self.birth_year = 2013
        self.birth_month = 11
        self.birth_day = 20
        self.type_filter_reg = '.(jpg|mp4|png|mov)$'
        self.master_list = {}

    def _parse_master_list(self) -> None:
        """step 1,get master_list
        """
        path_setting_correct_flag = True
        if self.path_of_folder_to_be_pasted:
            if self.path_of_folders_to_be_searched:
                logging.debug('Folder to be searched and folder to be pasted are configured.')
                if os.path.exists(self.path_of_folder_to_be_pasted):
                    logging.debug('Find folder to be pasted.')
                else:
                    logging.error('Failed to find folder to be pasted')
                    path_setting_correct_flag = False
                for tmp_path in self.path_of_folders_to_be_searched:
                    if os.path.exists(tmp_path):
                        logging.debug('Find %s' % tmp_path)
                    else:
                        logging.error('Failed to find %s' % tmp_path)
                        path_setting_correct_flag = False
            else:
                logging.error('No Config : folder to be searched & folder to be pasted.')
                path_setting_correct_flag = False
            if not path_setting_correct_flag:
                logging.error('Path config error. Script stops.')
                os._exit(1)
            for one_folder_to_be_searched in self.path_of_folders_to_be_searched:
                for current_folder_path, sub_folder_name, files_name in os.walk(one_folder_to_be_searched):
                    for one_file_name in files_name:
                        full_path_of_one_file = os.path.join(current_folder_path, one_file_name)
                        self.master_list[full_path_of_one_file] = [''] * 5
                        logging.debug('File is %s' % full_path_of_one_file)
                        last_edit_time = self._get_last_edit_time(one_file_name,full_path_of_one_file)
                        self.master_list[full_path_of_one_file][0] = last_edit_time
                        logging.debug('LastEditTime is %s' % self.master_list[full_path_of_one_file][0])
                        original_folder_path = current_folder_path
                        self.master_list[full_path_of_one_file][1] = original_folder_path
                        logging.debug('OriginalFolderPath is %s' % self.master_list[full_path_of_one_file][1])
                        destination_folder_path = self._check_and_create_destination_folder(last_edit_time)
                        self.master_list[full_path_of_one_file][2] = destination_folder_path
                        logging.debug('DestinationFolderPath is %s' % self.master_list[full_path_of_one_file][2])
                        duplicate_or_unique = self._check_if_file_is_already_in_destination(one_file_name, last_edit_time, destination_folder_path)
                        self.master_list[full_path_of_one_file][3] = duplicate_or_unique
                        logging.debug('DuplicateOrUnique is %s' % self.master_list[full_path_of_one_file][3])
                        if not re.search(self.type_filter_reg, one_file_name, re.IGNORECASE):
                            self.master_list[full_path_of_one_file][4] = 'ignore:file_type'
                            logging.warning('%s is ignored due to its file type.' % full_path_of_one_file)
                        elif destination_folder_path.endswith('error'):
                            self.master_list[full_path_of_one_file][4] = 'ignore:wrong_last_edit_time'
                            logging.warning('%s is ignored due to file edited time is earlier than birth day.' % full_path_of_one_file)
                        elif duplicate_or_unique == 'duplicate':
                            self.master_list[full_path_of_one_file][4] = 'ignore:duplicate'
                            logging.warning('%s is ignored due to duplication.' % full_path_of_one_file)
                        else:
                            self.master_list[full_path_of_one_file][4] = 'good_to_go'
                            logging.info('%s is to be moved...' % full_path_of_one_file)

    def _get_last_edit_time(self, file_name: str, full_file_path: str) -> str:
        """get last modified time/shot time from different cameras/sources
        Args:
            file_name: file name only.
            full_file_path: path and name
        Returns:
            last_edit_time: it's a str: dt_object.strftime('%Y-%m-%d_%H:%M:%S')
        """
        format_match = {'huawei_mate':re.match('(VID|IMG)_(\d{8})_(\d{6}).(mp4|jpg)', file_name),
         'from_weixin':re.match('(mmexport)?(\d{13}).(jpg|mp4)', file_name)}
        if format_match['huawei_mate']:
            shot_time = format_match['huawei_mate'].group(2) + '_' + format_match['huawei_mate'].group(3)
            datetime_shot_time = datetime.strptime(shot_time, '%Y%m%d_%H%M%S')
            return datetime_shot_time.strftime('%Y-%m-%d_%H:%M:%S')
        elif format_match['from_weixin']:
            shot_time = str(format_match['from_weixin'].group(2))[:-3]
            strftime_shot_time = self._convert_time_stamp_to_time(int(shot_time))
            return strftime_shot_time
        elif self._get_exif_datetimeoriginal_info(full_file_path):
            datetimeoriginal=datetime.strptime(self._get_exif_datetimeoriginal_info(full_file_path),'%Y:%m:%d %H:%M:%S')
            return datetimeoriginal.strftime('%Y-%m-%d_%H:%M:%S')
        else:
            return self._convert_time_stamp_to_time(int(os.path.getmtime(full_file_path)))

    def _get_exif_datetimeoriginal_info(self,full_file_path: str) -> str:
        """try to get exif info from pictures shot by DSLR,Mi 8,iphone,etc.
        Args:
            full_file_path: path and name
        Returns:
            return datetimeoriginal ('%Y:%m:%d %H:%M:%S') if it's found. Otherwise return None.
        """
        try:
            ret={}
            i=Image.open(full_file_path)
            info = i._getexif()
            for tag, value in info.items():
                decoded = TAGS.get(tag,tag)
                ret[decoded] = value
            datetimeoriginal=ret['DateTimeOriginal']
            if datetimeoriginal:
                return datetimeoriginal
            else:
                return None
        except:
            logging.info(f'Failed to get exif of image {full_file_path} ')
            return None


    def _convert_time_stamp_to_time(self, time_stamp: int) -> str:
        """convert 10 digits time_stamp to time
        """
        dt_object = datetime.fromtimestamp(time_stamp)
        logging.debug('dt_object = %s' % dt_object)
        return dt_object.strftime('%Y-%m-%d_%H:%M:%S')

    def _check_and_create_destination_folder(self, last_edit_time: str) -> str:
        """return destination folder to be pasted. creates one if it's needed.
        Args:
            last_edit_time: dt_object.strftime('%Y-%m-%d_%H:%M:%S')
        Returns:
            if ok: folder_path, folder 格式使用“.../20141120-20151119 (1-2岁合集)/20141120-20141219 (1岁0个月)”
            if last_edit_time is earlier than birth day: return '.../last_modified_time_error'.
        """
        month_frame = self._define_month_frame_for_subfolder(last_edit_time)
        year_frame = self._define_year_frame_for_subfolder(last_edit_time)
        age_years = None
        age_months = None
        if not str(month_frame).endswith('error'):
            age_years, age_months = self._get_age_year_month(last_edit_time)
            return self.path_of_folder_to_be_pasted + os.sep + year_frame + ' ' + '(' + str(age_years) + '-' + str(age_years + 1) + '岁合集)' + os.sep + month_frame + ' (' + str(age_years) + '岁' + str(age_months) + '个月)'
        else:
            return 'C:/fake/last_modified_time_error'

    def _get_age_year_month(self, last_edit_time: str) -> tuple:
        """
        Args:
            last_edit_time: dt_object.strftime('%Y-%m-%d_%H:%M:%S')
        Returns:
            return (years of age,months of age), 5岁3个月之类的
        """
        datetime1_last_edit_time = datetime.strptime(last_edit_time, '%Y-%m-%d_%H:%M:%S')
        str_birth_time = str(self.birth_year).zfill(4) + '-' + str(self.birth_month).zfill(2) + '-' + str(self.birth_day).zfill(2)
        datetime2_birth = datetime.strptime(str_birth_time, '%Y-%m-%d')
        time_diff = relativedelta(datetime1_last_edit_time, datetime2_birth)
        return (
         time_diff.years, time_diff.months)

    def _define_year_frame_for_subfolder(self, last_edit_time: str) -> str:
        """
        Args:
            last_edit_time: dt_object.strftime('%Y-%m-%d_%H:%M:%S')
        Returns:
            if ok: return year_frame like: '20131120-20141119'. 17 chars totally !
            if last_edit_time is earlier than birth day: return 'last_modified_time_error'.
        """
        str_birth_date = str(self.birth_year).zfill(4) + '-' + str(self.birth_month).zfill(2) + '-' + str(self.birth_day).zfill(2)
        birth_date = datetime.strptime(str_birth_date, '%Y-%m-%d')
        last_edit_date = datetime.strptime(last_edit_time.split('_')[0], '%Y-%m-%d')
        date2_birth_day_minus_one_day = birth_date + relativedelta(days=(-1))
        if last_edit_date < birth_date:
            logging.error('Last edit time is earlier than birth time. Please check.')
            return 'last_modified_time_error'
        elif int(last_edit_date.month) * 100 + int(last_edit_date.day) < self.birth_month * 100 + self.birth_day:
            return str(int(last_edit_date.year) - 1).zfill(4) + str(self.birth_month).zfill(2) + str(self.birth_day).zfill(2) + '-' + str(last_edit_date.year).zfill(4) + str(date2_birth_day_minus_one_day.month).zfill(2) + str(date2_birth_day_minus_one_day.day).zfill(2)
        else:
            return str(last_edit_date.year).zfill(4) + str(self.birth_month).zfill(2) + str(self.birth_day).zfill(2) + '-' + str(int(last_edit_date.year) + 1).zfill(4) + str(date2_birth_day_minus_one_day.month).zfill(2) + str(date2_birth_day_minus_one_day.day).zfill(2)

    def _define_month_frame_for_subfolder(self, last_edit_time: str) -> str:
        """
        Args:
            last_edit_time: dt_object.strftime('%Y-%m-%d_%H:%M:%S')
        Returns:
            if ok: return date_frame like: '20131120-20131220'. 17 chars totally !
            if last_edit_time is earlier than birth day: return 'last_modified_time_error'.
        """
        str_birth_date = str(self.birth_year).zfill(4) + '-' + str(self.birth_month).zfill(2) + '-' + str(self.birth_day).zfill(2)
        birth_date = datetime.strptime(str_birth_date, '%Y-%m-%d')
        last_edit_date = datetime.strptime(last_edit_time.split('_')[0], '%Y-%m-%d')
        date2_birth_day_minus_one_day = birth_date + relativedelta(days=(-1))
        if last_edit_date < birth_date:
            return 'last_modified_time_error'
        else:
            if last_edit_date.day < birth_date.day:
                if last_edit_date.month == 1:
                    return str(last_edit_date.year - 1).zfill(4) + '12' + str(self.birth_day).zfill(2) + '-' + str(last_edit_date.year).zfill(4) + str(last_edit_date.month).zfill(2) + str(date2_birth_day_minus_one_day.day).zfill(2)
                else:
                    return str(last_edit_date.year).zfill(4) + str(last_edit_date.month - 1).zfill(2) + str(self.birth_day).zfill(2) + '-' + str(last_edit_date.year).zfill(4) + str(last_edit_date.month).zfill(2) + str(date2_birth_day_minus_one_day.day).zfill(2)
            elif last_edit_date.month == 12:
                return str(last_edit_date.year).zfill(4) + str(last_edit_date.month).zfill(2) + str(self.birth_day).zfill(2) + '-' + str(last_edit_date.year + 1).zfill(4) + '01' + str(date2_birth_day_minus_one_day.day).zfill(2)
            return str(last_edit_date.year).zfill(4) + str(last_edit_date.month).zfill(2) + str(self.birth_day).zfill(2) + '-' + str(last_edit_date.year).zfill(4) + str(last_edit_date.month + 1).zfill(2) + str(date2_birth_day_minus_one_day.day).zfill(2)

    def _check_if_file_is_already_in_destination(self, file_name: str, last_edit_time_of_source_file: str, des_folder: str) -> str:
        """
        Args:
            last_edit_time_of_source_file: it's a str. dt_object.strftime('%Y-%m-%d_%H:%M:%S')
        Returns:
            "unique" if no duplication.
            "duplicate" if source file is already in destination folder.
        """
        if not os.path.exists(des_folder):
            return 'unique'
        else:
            if file_name in os.listdir(des_folder):
                full_path_of_des_file = os.path.join(des_folder, file_name)
                last_edit_time_of_des_file=self._get_last_edit_time(file_name,full_path_of_des_file)
                if last_edit_time_of_des_file == last_edit_time_of_source_file:
                    return 'duplicate'
                else:
                    return 'unique'
            else:
                return 'unique'

    def check_without_running(self) -> None:
        """get self.master_list,print and check the result.
           if everything is ok, then it's ok to execute final_run()
        """
        self._parse_master_list()
        if os.path.exists('result.csv'):
            os.remove('result.csv')
        with open ('result.csv','a+') as f:
            f.write('source_file,last_edit_time,original_folder,destination_folder,duplication_flag,action')
            f.write(os.linesep)
            for key_sourcefile,dict_values in self.master_list.items():
                f.write(key_sourcefile+',')
                for each_value in dict_values:
                    f.write(each_value+',')
                f.write(os.linesep)

    def check_and_run(self) -> None:
        """execute this whole script
           self.masterlist={'source_file':[last_edit_time,original_folder,destination_folder,duplication_flag,action]}
        """
        self.check_without_running()
        try:
            for key_sourcefile,dict_values in self.master_list.items():
                if dict_values[4] == 'good_to_go':
                    if not os.path.exists(dict_values[2]):
                        os.makedirs(dict_values[2])
                    shutil.copy(key_sourcefile,dict_values[2])
                    logging.debug(f'{key_sourcefile} is copied')
        except:
           logging.error('Failed to copy original file to destination.')
           logging.error('Maybe authority problem.')
           os._exit(1)



if __name__ == '__main__':
    set_up_logging(logging.DEBUG)
    mmp = Manage_Mi_Pics()
    mmp.birth_year = 2013
    mmp.birth_month = 11
    mmp.birth_day = 20
    mmp.type_filter_reg = '.(jpg|mp4|png|mov)$'
    mmp.path_of_folder_to_be_pasted = '/Users/ziwen/Documents/MyPic/Finish_bkp'
    mmp.path_of_folders_to_be_searched = ['/Users/ziwen/Documents/MyPic/Finish']
    mmp.check_and_run()
