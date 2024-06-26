import json
import random
from django.conf import settings
import os, sys
sys.path.append('../../backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'se_project.settings')

import django
django.setup()


class RecommendorPreparer():
    """The RecommendorPreparer class to prepare the courses for the students.

    """
    def __init__(self):
        """Initialize the RecommendorPreparer class.
        """
        pass
    
    def check_core_taken(self, course_num, course_name, ny_core_courses, sh_core_courses, taken_map):
        """ Check whether the core course is taken.

        Args:
            course_num (str): The course number.
            course_name (str): The course name.
            ny_core_courses (dict): The NY core courses.
            sh_core_courses (dict): The SH core courses.
            taken_map (dict): The taken map.

        Returns:
            int: The credits of the course.
        """
        # clean the course number
        course_num_idx = course_num.find('-')
        course_num_idx = course_num[course_num_idx+1:].find('-') + course_num_idx

        course_num = course_num[:course_num_idx] + course_num[course_num_idx+2:]
        
        find = False
        # find through ny core courses
        for core, core_courses in ny_core_courses.items():
            for core_course in core_courses:
                if course_num in core_course[0]:
                    taken_map[core] += 1
                    find = True
                    return int(core_course[2])
        
        # find through sh core courses
        if not find:
            for core, core_courses in sh_core_courses.items():
                for core_course in core_courses:
                    if course_num in core_course[0]:
                        taken_map[core] += 1
                        find = True
                        # shanghai core always has 4 credits
                        return 4

        return 0

    def filter_core_courses(self, course_history, ny_core_courses, sh_core_courses):
        """Filter out the left core courses that need to be taken.

        Args:
            course_history (dict): The course history of the student.
            ny_core_courses (dict): The NY core courses.
            sh_core_courses (dict): The SH core courses.
        
        Returns:
            list: The untaken core courses.
        """

        core_map = {
            'Algorithmic Thinking': 'AT',
            'Experimental Discovery in the Natural World': 'ED',
            'Humanistic Perspectives on China/China Arts-HPC/CA': 'HPC',
            'Interdisciplinary Perspectives on China': 'IPC',
            'Language': 'Language',
            'Math': 'Math',
            'Science, Technology and Society': 'STS',
            'Social Science Perspective on China': 'SSPC'
        }

        # 1 ED, 1STS, No Math (Assume we all place in to Calculus), 1AT, (IPC + HPC + SSPC) = 2
        taken_map = {'ED': 0, 'STS': 0, 'MATH': 0, 'AT': 0, 'IPC': 0, 'HPC': 0, 'SSPC': 0}

        total_credits = 0
        for _, taken_courses in course_history.items():
            for taken_course in taken_courses:
                if 'math' in taken_course[0].lower() and taken_map['MATH'] == 0:
                    total_credits += 4
                    taken_map['MATH'] = 1
                    continue
                # check if the taken course in the required courses
                # do not use the course name to search because the course name may be different
                # eg. in course history the `Computer Science Senior Project` is 
                total_credits += self.check_core_taken(taken_course[0], taken_course[1], ny_core_courses, sh_core_courses, taken_map)

        untaken_core_courses = []

        core_part1 = ['ED', 'STS', 'AT', 'MATH']
        core_part2 = ['IPC', 'HPC', 'SSPC']
        for core in core_part1:
            if taken_map[core] == 0:
                untaken_core_courses.append(core)
        
        if taken_map['IPC'] + taken_map['HPC'] + taken_map['SSPC'] < 2:
            untaken_core_courses.append('HPC')

        return untaken_core_courses

    def check_elective_taken(self, course_num, course_name, ny_elective_courses, sh_elective_courses, taken_elective):
        """Check whether the elective course is taken.

        Args:
            course_num (str): The course number.
            course_name (str): The course name.
            ny_elective_courses (list): The NY elective courses.
            sh_elective_courses (list): The SH elective courses.
            taken_elective (list): The taken electives.

        Returns:
            None
        """


        # clean the course number
        course_num_idx = course_num.find('-')
        course_num_idx = course_num[course_num_idx+1:].find('-') + course_num_idx

        course_num = course_num[:course_num_idx] + course_num[course_num_idx+2:]

        # find through sh electives
        if course_num[course_num.find('-')+1:course_num.find('-')+4] == 'SHU':
            # SH courses: (course_num, course_name, pre_reqs, credits)
            for elective_course in sh_elective_courses:
                if course_num == elective_course[0]:
                    taken_elective.append(course_num)
        else:
            # find through ny core courses
            # NY courses: (course_num, course_name, credits)
            for elective_course in ny_elective_courses:
                if course_num == elective_course[0]:
                    taken_elective.append(course_num)

    def filter_elective_courses(self, course_history, ny_electives, sh_electives):
        """Filter out the left elective courses that need to be taken.

        Args:
            course_history (dict): The course history of the student.
            ny_electives (list): The NY elective courses.
            sh_electives (list): The SH elective courses.

        Returns:
            list: The taken electives.
        """
        # store the taken electives
        taken_electives = []
        for _, taken_courses in course_history.items():
            for taken_course in taken_courses:
                # check if the taken course in the required courses
                # course_num: taken_course[0], course_name: taken_course[1]
                self.check_elective_taken(
                    taken_course[0], taken_course[1],
                    ny_electives, sh_electives,
                    taken_electives
                )
        
        return taken_electives

    def general_prepare(self, course_history, cs_major_courses, 
                        ny_core_courses, sh_core_courses,
                        ny_elective_courses, sh_elective_courses):
        """General prepare the courses for the students.

        Args:
            course_history (dict): The course history of the student.
            cs_major_courses (list): The CS major courses.
            ny_core_courses (dict): The NY core courses.
            sh_core_courses (dict): The SH core courses.
            ny_elective_courses (list): The NY elective courses.
            sh_elective_courses (list): The SH elective courses.

        Returns:
            tuple: The untaken core courses and taken electives.
        """

        # filter out the left core courses that need to be taken
        """
        sample untaken_core_courses:
        ['ED', 'HPC']
        """
        untaken_core_courses = self.filter_core_courses(course_history, ny_core_courses, sh_core_courses)

        # filter out the left elective courses that need be taken
        """
        sample taken_electives:
        ['CSCI-SHU 360', 'DATS-SHU 240']
        """
        taken_electives = self.filter_elective_courses(course_history, ny_elective_courses, sh_elective_courses)

        return untaken_core_courses, taken_electives


class Recommendor():
    """Recommendor class to recommend the courses for the students.
    """
    def __init__(self, course_history, identity, tense=False):
        """Initialize the Recommendor class.

        Args:
            course_history (dict): The course history of the student.
            identity (str): The identity of the student.
            tense (bool): Whether the student is in the tense mode (take as much electives as possible).
        
        Returns:
            None
        """
        # initialize the RecommendorPreparer
        self.recommendor_preparer = RecommendorPreparer()

        # identity: ['chinese', 'inter']
        # general framework for the courses
        if identity == 'chinese':
            self.recommend_template = {
                'freshmen_1st': ['Language', 'GPS'],
                'freshmen_2nd': ['Language', 'WAI',],
                'sophomore_1st': ['POH'],
                'senior_1st': ['Capstone']
            }
        else:
            self.recommend_template = {
                'freshmen_1st': ['Language', 'GPS'],
                'freshmen_2nd': ['Language', 'WAI'],
                'sophomore_1st': ['Language', 'POH'],
                'sophomore_2nd': ['Language'],
                'senior_1st': ['Capstone']
            }

        # 0: icp, 1: calculus, 2: ics. 3: prob and stat, 4: discrete, 5: arch, 6: data structure, 7: os, 8: algo
        self.semesters = ['freshmen_1st', 'freshmen_2nd', 'sophomore_1st', 'sophomore_2nd', 'junior_1st', 'junior_2nd', 'senior_1st', 'senior_2nd']
        self.course_history = course_history

        with open(os.path.join(settings.BASE_DIR, 'courses/recommendor/cs_major_courses.json'), 'r') as json_file:
            self.cs_major_courses = json.load(json_file)

        self.major_course_list = [0, 1, 2, 3, 4, 5, 6, 7, 8]
        self.major_course_pre_reqs = {0: [], 1: [], 2: [0], 3: [1], 4: [1], 5: [2], 6: [2], 7: [5], 8: [6, 4]}

        # whether open the JuanWang mode
        self.tense = tense

        # stores the indices of the self.cs_major_courses
        """
        sample untaken_major_courses: 
        [
            idx of ['CSCI-SHU 220 Algorithms', 'CS-UY 2413 Design & Analysis of Algorithms', 'CSCI-GA 1170 Fundamental Algorithms', 'CSCI-UA 310 Basic Algorithms'],
            idx of ['CSCI-SHU 420 Computer Science Senior Project']
        ]
        """
        self.untaken_major_courses = self._init_recommend()

    def clean_course_number(self, course_number):
        """Clean the course number.

        Args:
            course_number (str): The course number.
        
        Returns:
            str: The cleaned course number.
        """
        if course_number.count('-') == 1:
            return course_number

        # clean the course number
        course_num_idx = course_number.find('-')
        course_num_idx = course_number[course_num_idx+1:].find('-') + course_num_idx

        return course_number[:course_num_idx] + course_number[course_num_idx+2:]

    def _init_recommend(self):
        """Initialize the recommendor.

        Returns:
            list: The untaken major courses.
        """
        semesters = list(self.course_history.keys())
        semesters.reverse()

        taken_major_courses = []

        # iterate through out the semester
        for semester in semesters:
            # get the each taken course
            for taken_course in self.course_history[semester]:
                # find whether the course is in the major course list
                for major_courses_idx in range(len(self.cs_major_courses)):
                    for major_course in self.cs_major_courses[major_courses_idx]:
                        if self.clean_course_number(taken_course[0]) in major_course:
                            taken_major_courses.append(major_courses_idx)
                            break

        taken_major_courses.sort()
        untaken_major_courses = list(set(self.major_course_list) - set(taken_major_courses))
        untaken_major_courses.sort()
        
        return untaken_major_courses

    def validate_elective(self, elective):
        """ Validate the elective course.

        Args:
            elective (list): The elective course.
        
        Returns:
            bool: Whether the elective course is valid.
        """
        pre_reqs = elective[2]
        is_valid = True

        # find each prerequite
        for pre_req in pre_reqs:
            find = False
            # find through the taken courses
            for semester in self.course_history.keys():
                for taken_course in self.course_history[semester]:
                    if self.clean_course_number(taken_course[0]) in pre_req:
                        find = True

            # update the is_valid for each prerequite
            is_valid = is_valid and find

        return is_valid

    def recommend(self):
        """Recommend the courses for the students.

        Returns:
            bool: Whether the student can graduate.
        """
        # load the ny core courses
        with open(os.path.join(settings.BASE_DIR, 'courses/recommendor/ny_core_courses.json'), 'r') as json_file:
            ny_core_courses = json.load(json_file)
    
        # load the ny elective courses
        with open(os.path.join(settings.BASE_DIR,'courses/recommendor/ny_elective_courses.json'), 'r') as json_file:
            ny_elective_courses = json.load(json_file)

        # load the sh elective courses
        with open(os.path.join(settings.BASE_DIR,'courses/recommendor/sh_elective_courses.json'), 'r') as json_file:
            sh_elective_courses = json.load(json_file)

        # load sh core courses
        with open(os.path.join(settings.BASE_DIR, 'courses/recommendor/sh_core_courses.json'), 'r') as json_file:
            sh_core_courses = json.load(json_file)

        # prepare the untaken core courses and taken electives
        self.untaken_core_courses, self.taken_electives = self.recommendor_preparer.general_prepare(
            self.course_history, self.cs_major_courses, ny_core_courses, sh_core_courses, ny_elective_courses, sh_elective_courses
        )

        if len(self.course_history.keys()) == 8:
            return None

        recommend = {}
        rest_semesters = self.semesters[len(self.course_history.keys()):]
        for rest_semester in rest_semesters:
            # first try to find through the recommend template
            try:
                recommend_courses = self.recommend_template[rest_semester]
            except:
                recommend_courses = []
            # recommend append type: f'{course num} {course name}'

            # indicate whether enroll in the NY courses
            if rest_semester == 'junior_1st' or rest_semester == 'junior_2nd':
                ny = True
            else:
                ny = False

            # we simply recommend half of the courses be the core courses
            # half of the courses be the major courses
            core_recommend_limit = int((4 - len(recommend_courses)) / 2)
            core_recommend_count = 0

            # special care for the case that we didn't take the Math and AT
            if 'MATH' in self.untaken_core_courses and 'AT' in self.untaken_core_courses:
                if core_recommend_limit == 1 and len(recommend_courses) + core_recommend_limit <= 4:
                    core_recommend_limit = 2

            # recommend the core courses
            if len(self.untaken_core_courses) > 0:
                # top core pirority: Math: Calculus and AT: ICP
                if 'MATH' in self.untaken_core_courses and core_recommend_count < core_recommend_limit:
                    if ny:
                        # find in ny courses
                        for course in self.cs_major_courses[1]:
                            if 'UA' in course:
                                recommend_courses.append(f'{course} | Math core')
                                break
                    else:
                        # find in sh courses
                        for course in self.cs_major_courses[1]:
                            if 'SHU' in course:
                                recommend_courses.append(f'{course} | Math core')
                                break
                    
                    # update the untakne core courses
                    self.untaken_core_courses.remove('MATH')

                    core_recommend_count += 1

                    # update the untakne major courses
                    self.untaken_major_courses.remove(1)

                if 'AT' in self.untaken_core_courses and core_recommend_count < core_recommend_limit:
                    if ny:
                        # find in ny courses
                        for course in self.cs_major_courses[1]:
                            if 'UA' in course:
                                recommend_courses.append(f'{course} | AT core')
                                break
                    else:
                        # find in sh courses
                        for course in self.cs_major_courses[1]:
                            if 'SHU' in course:
                                recommend_courses.append(f'{course} | AT core')
                                break
                    
                    # update the untakne core courses
                    self.untaken_core_courses.remove('AT')

                    core_recommend_count += 1

                    # update the untakne major courses
                    self.untaken_major_courses.remove(0)

                # recomend one more core courses
                if core_recommend_count < core_recommend_limit:
                    # extract the core type and update the self.untaken_core_courses
                    core_type = self.untaken_core_courses.pop(0)

                    # randomly choose the course to add diversity
                    # no worries of the repeat courses, we recommend the untaken core
                    if ny:
                        # find in ny courses
                        course = random.choice(ny_core_courses[core_type])
                    else:
                        # find in sh courses
                        course = random.choice(sh_core_courses[core_type])

                    recommend_courses.append(f'{course[0]} {course[1]} | {core_type} core')

            # recommend the major courses
            # we do this by a greedy way by giving the major course the proper indices
            if len(self.untaken_major_courses) > 0 and len(recommend_courses) < 4:
                current_semester_majors = []
                # we simply recommend half of the courses be the major courses
                major_recommend_num = min(4 - len(recommend_courses), len(self.untaken_major_courses))

                for i in range(major_recommend_num):
                    # extract the major idx and update the self.untaken_major_courses
                    major_type_idx = self.untaken_major_courses[0]

                    # check the major requirement
                    valid = True
                    for i in self.major_course_pre_reqs[major_type_idx]:
                        if i in self.untaken_major_courses or i in current_semester_majors:
                            valid = False

                    if not valid:
                        break

                    # update the untakne major courses only when this type is valid
                    self.untaken_major_courses.pop(0)
                    current_semester_majors.append(major_type_idx)

                    # randomly choose the course to add diversity
                    if ny:
                        # find in NY courses
                        for courses in self.cs_major_courses[major_type_idx]:
                            if 'UA' in courses:
                                recommend_courses.append(courses)
                                break
                    else:
                        # find in SH courses
                        for courses in self.cs_major_courses[major_type_idx]:
                            if 'SHU' in courses:
                                recommend_courses.append(courses)
                                break

            # recommend the electives
            if len(recommend_courses) < 4 and len(self.taken_electives) < 5:
                for i in range(4 - len(recommend_courses)):
                    # randomly choose the course to add diversity
                    if ny:
                        # find in NY courses, we can't get the prerequite courses
                        # so we randomly choose the course
                        find = False
                        while not find:
                            course = random.choice(ny_elective_courses)
                            # check if the course is already taken
                            if course[0] in self.taken_electives:
                                find = False
                            else:
                                find = True

                            recommend_courses.append(f'{course[0]} {course[1]}')
                            # update the taken electives
                            self.taken_electives.append(course[0])
                    else:
                        # find in SH courses
                        for course in sh_elective_courses:
                            if course[0] not in self.taken_electives and self.validate_elective(course):
                                recommend_courses.append(f'{course[0]} {course[1]}')
                                # update the taken electives
                                self.taken_electives.append(course[0])
                                break
            elif len(recommend_courses) < 4:
                if not self.tense:
                    elective_num = 1
                else:
                    # if the tense is True, all left courses are filled with elective courses
                    elective_num = 4 - len(recommend_courses)

                for i in range(elective_num):
                    # only recommend one elective per semester
                    if ny:
                        # find in NY courses, we can't get the prerequite courses
                        # so we randomly choose the course
                        find = False
                        while not find:
                            course = random.choice(ny_elective_courses)
                            # check if the course is already taken
                            if course[0] in self.taken_electives:
                                find = False
                            else:
                                find = True

                            # update the taken electives
                            self.taken_electives.append(course[0])
                    else:
                        # find in SH courses
                        for course in sh_elective_courses:
                            if course[0] not in self.taken_electives and self.validate_elective(course):
                                recommend_courses.append(f'{course[0]} {course[1]}')
                                # update the taken electives
                                self.taken_electives.append(course[0])
                                break
            
            # if there are still left spaces for recommendation
            # fill with 'Your Choice'
            if len(recommend_courses) < 4:
                for i in range(4 - len(recommend_courses)):
                    recommend_courses.append('Your Choice')

            recommend[rest_semester] = recommend_courses

            # update the course_history
            self.course_history[rest_semester] = recommend_courses

        # after recommendation, if there are still left untaken core/major courses, the taken electives are not 4
        # this is not the regular cases and we recommend the user to arange by themselves
        if len(self.untaken_core_courses) > 0 or len(self.untaken_major_courses) > 0 or len(self.taken_electives) < 4:
            return False, recommend
        else:
            return True, recommend