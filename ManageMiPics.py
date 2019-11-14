"""此文件用于整理米仔的照片到相应的folder。
之前有手动创建过一些folder，用folder前十七位“20131120-20131220”作为目标时间段
没有手动创建的folder，自动创建，格式使用“.../20141120-20151120 (1岁合集)/20141120-20141220 （1岁1个月）”
其他照片或视频，以文件的LastModifiedTime 作为标准，将照片转入相应folder内。
有些单反拍摄的文件，时间可能不对。
"""
import os
import re
import logging
import time
from datetime import datetime
from dateutil.relativedelta import relativedelta
from typing import List,Callable,Sequence,TypeVar
T = TypeVar('T')

def set_up_logging(level:int) -> None:
    """
    Args:
        level:logging.DEBUG,logging.INFO,etc. Logging level configuration.
    """
    logging.basicConfig(level = level,format = '%(asctime)s [line:%(lineno)d] %(levelname)s: %(message)s', datefmt='%d %b %H:%M:%S')
    logger = logging.getLogger(__name__)


class Manage_Mi_Pics():
    """
    处理照片的类。
    所有数据，被解析到下面这个字典里面：
    master_list={'picture_location':['LastEditTime','OriginalFolderPath','DestinationFolderPath','DuplicateOrUnique','Action']}
    """

    @property
    def path_of_folders_to_be_searched(self) -> List:
        return self._path_of_folders_to_be_searched

    @path_of_folders_to_be_searched.setter
    def path_of_folders_to_be_searched(self,path_of_folders:List) -> None:
        self._path_of_folders_to_be_searched=path_of_folders

    @property
    def path_of_folder_to_be_pasted(self) -> str:
        return self._path_of_folder_to_be_pasted

    @path_of_folder_to_be_pasted.setter
    def path_of_folder_to_be_pasted(self,path_of_folder:str) -> None:
        self._path_of_folder_to_be_pasted=path_of_folder

    def __init__(self) -> None:
        self._path_of_folders_to_be_searched=[]
        self._path_of_folder_to_be_pasted=None
        self._birth_year=2013
        self._birth_month=11
        self._birth_day=20
        self.master_list={}

    def _get_required_files_path(self, type_filter_reg:str =r'.(jpg|mp4|png|mov)$') -> None:
        """
        Args:
            type_filter_reg: regular expresion to filter required file.
        """
        path_setting_correct_flag=True
        if (self._path_of_folder_to_be_pasted and self._path_of_folders_to_be_searched):
            logging.debug ('Folder to be searched and folder to be pasted are configured.')
            if os.path.exists(self._path_of_folder_to_be_pasted):
                logging.debug('Find folder to be pasted.')
            else:
                logging.error('Failed to find folder to be pasted')
                path_setting_correct_flag=False
            for tmp_path in self._path_of_folders_to_be_searched:
                if os.path.exists(tmp_path):
                    logging.debug('Find %s'%tmp_path)
                else:
                    logging.error('Failed to find %s'%tmp_path)
                    path_setting_correct_flag=False
        else:
            logging.error ('Config folder to be searched and folder to be pasted.')
            path_setting_correct_flag=False

        if path_setting_correct_flag:
            logging.debug ('Continue...')
        else:
            logging.error ('Path config error. Script stops.')
            os._exit(1)

        for one_folder_to_be_searched in self._path_of_folders_to_be_searched:
            for (current_folder_path, sub_folder_name, files_name) in os.walk(one_folder_to_be_searched):
                for one_file_name in files_name:
                    full_path_of_one_file=os.path.join(current_folder_path,one_file_name)
                    self.master_list[full_path_of_one_file]=['']*5
                    logging.debug ('File is %s'%full_path_of_one_file)
                    last_edit_time=self._convert_time_stamp_to_time(int(os.path.getmtime(full_path_of_one_file)))
                    self.master_list[full_path_of_one_file][0]=last_edit_time
                    logging.debug ('LastEditTime is %s'%self.master_list[full_path_of_one_file][0])
                    original_folder_path=current_folder_path
                    self.master_list[full_path_of_one_file][1]=original_folder_path
                    logging.debug ('OriginalFolderPath is %s'%self.master_list[full_path_of_one_file][1])
                    destination_folder_path=self._check_and_create_destination_folder(last_edit_time)
                    self.master_list[full_path_of_one_file][2]=destination_folder_path
                    logging.debug ('DestinationFolderPath is %s'%self.master_list[full_path_of_one_file][2])
                    duplicate_or_unique=self._check_if_file_is_already_in_destination(one_file_name,last_edit_time,destination_folder_path)
                    self.master_list[full_path_of_one_file][3]=duplicate_or_unique
                    logging.debug ('DuplicateOrUnique is %s'%self.master_list[full_path_of_one_file][3])

                    if (not re.search(type_filter_reg,one_file_name,re.IGNORECASE)):
                        self.master_list[full_path_of_one_file][4]='ignore:file_type'
                        logging.warning ('%s is ignored due to its file type.'%full_path_of_one_file)
                    elif(destination_folder_path.endswith('error')):
                        self.master_list[full_path_of_one_file][4]='ignore:wrong_edit_time'
                        logging.warning ('%s is ignored due to file edited time is earlier than birth day.'%full_path_of_one_file)
                    elif (duplicate_or_unique=='duplicate'):
                        self.master_list[full_path_of_one_file][4]='ignore:duplicate'
                        logging.warning ('%s is ignored due to duplication.'%full_path_of_one_file)
                    else:
                        self.master_list[full_path_of_one_file][4]='' #leave action as blank if everything is ok by now
                        logging.warning ('%s is to be moved...'%full_path_of_one_file)



    def _convert_time_stamp_to_time(self,time_stamp:int)->str:
        """convert 10 digits time_stamp to time
        """
        dt_object = datetime.fromtimestamp(time_stamp)
        logging.debug("dt_object = %s"%dt_object)
        return dt_object.strftime('%Y-%m-%d_%H:%M:%S')

    def _check_and_create_destination_folder(self, last_edit_time:str)->str:
        """return destination folder to be pasted. creates one if it's needed.
        Args:
            last_edit_time: dt_object.strftime('%Y-%m-%d_%H:%M:%S')
        Returns:
            if ok: folder_path, folder 格式使用“.../20141120-20151120 (1岁合集)/20141120-20141220 （1岁1个月）”
            if last_edit_time is earlier than birth day: return '.../last_modified_time_error'.
        """
        month_frame=self._define_month_frame_for_subfolder(last_edit_time)
        year_frame=self._define_year_frame_for_subfolder(last_edit_time)
        age_years=None
        age_months=None
        if(not str(month_frame).endswith('error')):
            (age_years,age_months)=self._get_age_year_month(last_edit_time)
            return r'C:/fake/'+year_frame+' '+r'('+str(age_years)+'岁合集)'+os.sep+month_frame+r' ('+str(age_years)+'岁'+str(age_months)+r'个月)'
        else:
            return r'C:/fake/last_modified_time_error'

    def _get_age_year_month(self,last_edit_time:str)->tuple:
        """
        Args:
            last_edit_time: dt_object.strftime('%Y-%m-%d_%H:%M:%S')
        Returns:
            return (years of age,months of age),  5岁3个月之类的
        """
        datetime1_last_edit_time=datetime.strptime(last_edit_time,'%Y-%m-%d_%H:%M:%S')
        birth_time=str(self._birth_year).zfill(4)+'-'+str(self._birth_month).zfill(2)+'-'+str(self._birth_day).zfill(2)+'_00:00:01'
        datetime2_birth=datetime.strptime(birth_time,'%Y-%m-%d_%H:%M:%S')
        time_diff=relativedelta(datetime1_last_edit_time,datetime2_birth)
        return (time_diff.years,time_diff.months)

    def _define_year_frame_for_subfolder(self,last_edit_time:str)->str:
        """
        Args:
            last_edit_time: dt_object.strftime('%Y-%m-%d_%H:%M:%S')
        Returns:
            if ok: return year_frame like: '20131120-20141120'. 17 chars totally !
            if last_edit_time is earlier than birth day: return 'last_modified_time_error'.
        """
        year=last_edit_time.split('-')[0]
        month=last_edit_time.split('-')[1]
        day=last_edit_time.split('-')[2].split('_')[0]
        date=year+month+day #e.g.20191022, 20170304...
        if (int(date)<int( (str(self._birth_year)+str(self._birth_month)+str(self._birth_day)) )):
            logging.error('Last edit time is earlier than birth time. Please check.')
            return 'last_modified_time_error'
        if ( (int(month)*100+int(day)) < (self._birth_month*100+self._birth_day)):
            return str(int(year)-1).zfill(4)+str(self._birth_month).zfill(2)+str(self._birth_day).zfill(2)+'-'+year+str(self._birth_month).zfill(2)+str(self._birth_day).zfill(2)
        else:
            return year+str(self._birth_month).zfill(2)+str(self._birth_day).zfill(2)+'-'+str(int(year)+1).zfill(4)+str(self._birth_month).zfill(2)+str(self._birth_day).zfill(2)

    def _define_month_frame_for_subfolder(self,last_edit_time:str)->str:
        """
        Args:
            last_edit_time: dt_object.strftime('%Y-%m-%d_%H:%M:%S')
        Returns:
            if ok: return date_frame like: '20131120-20131220'. 17 chars totally !
            if last_edit_time is earlier than birth day: return 'last_modified_time_error'.
        """
        year=last_edit_time.split('-')[0]
        month=last_edit_time.split('-')[1]
        day=last_edit_time.split('-')[2].split('_')[0]
        date=year+month+day #e.g.20191022, 20170304...
        if (int(date)<int( (str(self._birth_year)+str(self._birth_month)+str(self._birth_day)) )):
            return 'last_modified_time_error'
        if (int(day)<self._birth_day):
            if month=='01':
                return str(int(year)-1).zfill(4)+'12'+str(self._birth_day).zfill(2)+'-'+year+month+str(self._birth_day).zfill(2)
            else:
                return year+str(int(month)-1).zfill(2)+str(self._birth_day).zfill(2)+'-'+year+month+str(self._birth_day).zfill(2)
        else:
            if month=='12':
                return year+month+str(self._birth_day).zfill(2)+'-'+str(int(year)+1).zfill(4)+'01'+str(self._birth_day).zfill(2)
            else:
                return year+month+str(self._birth_day).zfill(2)+'-'+year+str(int(month)+1).zfill(2)+str(self._birth_day).zfill(2)


    def _check_if_file_is_already_in_destination(self,file_name:str,last_edit_time_of_source_file:str,des_folder:str) -> str:
        """
        Returns:
            "unique" if no duplication.
            "duplicate" if source file is already in destination folder.
        """
        return "unique"



    def _filter_create_timeframe(self,full_path_of_one_file:str,created_timeframe:List) ->  bool:
        """check if the file creating time is in the range or not
        Args:
            full_path_of_one_file
            created_timeframe:list like : ['2019-10-01 00-00-00','2019-10-02 23-59-59']
        Returns:
            if file creating time is in the range or not.
        """
        try:
            starting_time=time.mktime(time.strptime(created_timeframe[0],'%Y-%m-%d %H-%M-%S'))
            ending_time=time.mktime(time.strptime(created_timeframe[1],'%Y-%m-%d %H-%M-%S'))
            if starting_time > ending_time:
                raise
        except:
            logging.error('Failed to parse created_timeframe. Wrong format.')
            os._exit(1)
        else:
            file_created_time=os.path.getctime(full_path_of_one_file)
            if (file_created_time > starting_time and file_created_time < ending_time) :
                return True
            else:
                return False


    def run(self) -> None:
        """Interface of parsing. All parse functions need use this.
        """
        self._reset_params_before_parsing()
        if not self._parse_function:
            logging.error('No parse function is selected. Please asign .parse_function.')
            os._exit(1)
        else:
            self._write_csv_collumn_name(self._parse_function)
        for tmp_each_file in self._full_path_of_files:
            with open (tmp_each_file,mode='r',encoding='utf-8',errors='ignore') as f:
                contents=f.readlines()
                self._parse_function(file_location=tmp_each_file,lines=contents)
                f.close()

    def _reset_params_before_parsing(self) -> None:
        self._qty_of_count_required_info=0

    def _write_csv_collumn_name(self,function_name:Callable) -> None:
        if function_name == self.pull_info_with_two_specific_words:
            self._generate_csv_result(('File_location','Line_num','Contents'))
        else:
            logging.info('Use default csv collumn name')
            self._generate_csv_result(('File_location','Line_num','Contents'))

    def _generate_csv_result(self,csv_results:List) -> None:
        try:
            with open(self.result_csv_file,'a') as fcsv:
                for each_item in csv_results:
                    item_without_line_break=(str)(each_item).rstrip()
                    item_without_comma=item_without_line_break.replace(',',' ') #replace comma in original file as blank.
                    fcsv.write(item_without_comma +',')
                fcsv.write('\n')
                fcsv.close()
        except:
            logging.error('Failed to write result csv file.')
            logging.error('Stop program')
            os._exit(1)





if __name__=='__main__':
    set_up_logging(logging.DEBUG)
    mmp = Manage_Mi_Pics()
    mmp.path_of_folder_to_be_pasted=r'D:\Ziwen'
    mmp.path_of_folders_to_be_searched=[r'D:\Ziwen\Personal\pic',r'C:\Users\z003b4ys\Pictures']
    #mmp._get_required_files_path()





