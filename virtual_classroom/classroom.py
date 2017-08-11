from re import split

from student import Student
from send_email import Email, EmailBody, SMTPGoogle, SMTPUiO, connect_to_email_server
from parameters import get_parameters
from collaboration import start_peer_review
from get_all_repos import download_repositories
from api import APIManager


class Classroom(object):
    """Contains help functions to get an overveiw of the virtual classroom"""

    def __init__(self, file=None):
        self.students = {}
        self.collaboration = None
        self.review_groups = None
        if file is None:
            # TODO: Fetch default file
            return

        # Load parameters
        parameters = get_parameters()
        self.university = parameters["university"]
        self.course = parameters["course"]
        self.org = "%s-%s" % (self.university, self.course)

        lines = open(file, "r").readlines()
        # Create a dict with students
        for line in lines:
            try:
                present, name, username, email, _, _ = split(r"\s*\/\/\s*", line.replace('\n', ''))
                rank = 1
            except:
                present, name, username, email, _ = split(r"\s*\/\/\s*", line.replace('\n', ''))
                rank = 1
            if present.lower() == 'x' and username != "":
                print "Handle student {0}".format(name)
                self.students[name] = Student(name,
                                              username,
                                              self.university,
                                              self.course,
                                              email,
                                              rank)

    def start_peer_review(self, max_group_size=None, rank=None):
        parameters = get_parameters()
        # TODO: Consider renaming max_students to max_group_size
        max_group_size = parameters["max_students"] if max_group_size is None else max_group_size
        rank = parameters["rank"] if rank is None else rank

        self.review_groups = start_peer_review(self.students, max_group_size, rank)

    def end_peer_review(self):
        api = APIManager()
        teams = api.get_teams(self.org)

        number_deleted = 0
        number_not_deleted = 0
        not_deleted = ''
        for team in teams:
            if 'Team-' in team['name']:
                r = api.delete_team(team['id'])
                if r.status_code != 204:
                    number_not_deleted += 1
                    not_deleted += '\n' + team['name']
                else:
                    number_deleted += 1

        if number_not_deleted == 0:
            print('Deleted all teams related to the group session (%d teams deleted)' % \
                  number_deleted)
        else:
            print('Deleted %s teams, but there were %s teams that where not deleted:%s' % \
                  (number_deleted, number_not_deleted, not_deleted))

    def end_semester(self):
        # TODO: Also delete teams. Might benefit from iterating through self.students.
        api = APIManager()
        list_repos = api.get_repos(self.org)
        list_members = api.get_members(self.org, "member")

        for member in list_members:
            # if member['login'].encode('utf-8') in members_to_delete
            print("Deleting %s" % member["login"])
            r = api.delete_org_member(self.org, member["login"])
            print r.status_code

        # Delete repos
        for repo in list_repos:
            if self.course in repo['name']:
                print "Deleting repository ", self.org + repo['name']
                r = api.delete_repo(self.org, repo["name"])
                print r.status_code

    def download_repositories(self, directory):
        """Downloads all repositories in the classroom
        
        """
        download_repositories(directory)

    def email_students(self, filename, subject="", extra_params={}, smtp=None):
        """Sends an email to all students in the classroom.

        Will try to format the email body text with student attributes and `extra_params`.

        Parameters
        ----------
        filename : str
            Path to the file containing the email body text
        subject : str, optional
            Subject of the email
        extra_params : dict, optional
            Dictionary of extra parameters to format the email body text
        smtp : str, optional
            The SMTP server to use. Can either be 'google' or 'uio'.

        """
        server = connect_to_email_server(smtp)
        email_body = EmailBody(filename)
        email = Email(server, email_body, subject=subject)

        for name in self.students:
            student = self.students[name]
            params = student.__dict__.copy()
            params.update(extra_params)
            email_body.params = params
            email.send(student.email)

    def email_review_groups(self, filename, subject="", extra_params={}, smtp=None):
        """Sends an email to all review groups in the classroom.

        Will try to format the email body text with group attributes,
        student attributes and `extra_params`.

        Parameters
        ----------
        filename : str
            Path to the file containing the email body text
        subject : str, optional
            Subject of the email
        extra_params : dict, optional
            Dictionary of extra parameters to format the email body text
        smtp : str, optional
            The SMTP server to use. Can either be 'google' or 'uio'.

        """
        server = connect_to_email_server(smtp)
        email_body = EmailBody(filename)
        email = Email(server, email_body, subject=subject)

        for group in self.review_groups:
            params = group.__dict__.copy()
            for student in group.students:
                params.update(student.__dict__)
                params.update(extra_params)
                email_body.params = params
                email.send(student.email)






