from django.shortcuts import render    
from django.http import HttpResponseRedirect
from django.db.models import Q
# <HINT> Import any new Models here
from .models import Course, Enrollment, Question, Choice, Submission, Lesson
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.views import generic
from django.contrib.auth import login, logout, authenticate
import logging
# Get an instance of a logger
logger = logging.getLogger(__name__)
# Create your views here.

def registration_request(request):
    context = {}
    if request.method == 'GET':
        return render(request, 'onlinecourse/user_registration_bootstrap.html', context)
    elif request.method == 'POST':
        # Check if user exists
        username = request.POST['username']
        password = request.POST['psw']
        first_name = request.POST['firstname']
        last_name = request.POST['lastname']
        user_exist = False
        try:
            User.objects.get(username=username)
            user_exist = True
        except:
            logger.error("New user")
        if not user_exist:
            user = User.objects.create_user(username=username, first_name=first_name, last_name=last_name,
                                            password=password)
            login(request, user)
            return redirect("onlinecourse:index")
        else:
            context['message'] = "User already exists."
            return render(request, 'onlinecourse/user_registration_bootstrap.html', context)


def login_request(request):
    context = {}
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['psw']
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('onlinecourse:index')
        else:
            context['message'] = "Invalid username or password."
            return render(request, 'onlinecourse/user_login_bootstrap.html', context)
    else:
        return render(request, 'onlinecourse/user_login_bootstrap.html', context)


def logout_request(request):
    logout(request)
    return redirect('onlinecourse:index')


def check_if_enrolled(user, course):
    is_enrolled = False
    if user.id is not None:
        # Check if user enrolled
        num_results = Enrollment.objects.filter(user=user, course=course).count()
        if num_results > 0:
            is_enrolled = True
    return is_enrolled


# CourseListView
class CourseListView(generic.ListView):
    template_name = 'onlinecourse/course_list_bootstrap.html'
    context_object_name = 'course_list'

    def get_queryset(self):
        user = self.request.user
        courses = Course.objects.order_by('-total_enrollment')[:10]
        for course in courses:
            if user.is_authenticated:
                course.is_enrolled = check_if_enrolled(user, course)
        return courses


class CourseDetailView(generic.DetailView):
    model = Course
    template_name = 'onlinecourse/course_detail_bootstrap.html'


def enroll(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    user = request.user

    is_enrolled = check_if_enrolled(user, course)
    if not is_enrolled and user.is_authenticated:
        # Create an enrollment
        Enrollment.objects.create(user=user, course=course, mode='honor')
        course.total_enrollment += 1
        course.save()

    return HttpResponseRedirect(reverse(viewname='onlinecourse:course_details', args=(course.id,)))


# <HINT> Create a submit view to create an exam submission record for a course enrollment,
# you may implement it based on following logic:
         # Get user and course object, then get the associated enrollment object created when the user enrolled the course
         # Create a submission object referring to the enrollment
         # Collect the selected choices from exam form
         # Add each selected choice object to the submission object
         # Redirect to show_exam_result with the submission id
#def submit(request, course_id):
def submit(request, course_id):
    if request.method =='POST':
        #course = Course.objects.get(pk=course_id)
        user = request.user.id
        #enrollment = Enrollment.objects.filter(Q(user=user) & Q(course=course_id)).values_list('pk', flat=True)[0]
        enrollment = Enrollment.objects.filter(Q(user=user) & Q(course=course_id))[0]

        answers = extract_answers(request)
        #extract_answers(request)
        #answers = [1,3,2]


        submission = Submission(enrollment=enrollment)
        submission.save()
        for choice in answers:
            submission.chocies.add(choice)
            #print('The choice id is ')
            #print(choice)
        submission.save()
        #print('the submissioin record is:')
        #print(submission.id)
        print("the choices extracted by func are")
        for choice in submission.chocies.all():
            #print()
            print(choice)
        return HttpResponseRedirect(reverse(viewname='onlinecourse:show_exam_result', args=(course_id, submission.id,)))

# <HINT> A example method to collect the selected choices from the exam form from the request object
def extract_answers(request):
    submitted_anwsers = []
    print("hello out")
    for key in request.POST:
        print("hello for")
        if key.startswith('choice'):
            value = request.POST[key]
            #value = int(key)
            value = int(''.join(filter(str.isdigit, key)))
            print(value)
            #choice_id = int(value)
            print("hello")
            submitted_anwsers.append(value)
    some_var = request.POST.getlist('choice[]')
    print(some_var)
    for element in some_var:
        print("hello")
    print(request.POST)
    print('the submitted ansswers ids')
    print(submitted_anwsers)
    return submitted_anwsers

def question_exist(questions, the_question):
    exist = False
    for question in questions:
        if the_question == question:
            exist = True
    return exist

def number_of_correct_choices(question):
    number = 0
    choices = Choice.objects.filter(question_id=question)
    for choice in choices:
        if choice.is_correct:
            number += 1
    return number

def choice_is_selected(choice, submission_id):
    is_selected = False
    submission = Submission.objects.get(pk=submission_id)
    selected_choice_ids = submission.chocies.all()
    for id in selected_choice_ids:
        if id == choice:
            is_selected = True
    return is_selected
def get_quest_number(course_id):
    list_of_questions = []
    lessons = Lesson.objects.filter(course=course_id)
    for lesson in lessons:
        questions = Question.objects.filter(lesson_id=lesson.id)
        for question in questions:
            if question.id in list_of_questions:
                None
            else: 
                list_of_questions.append(question.id)
    return len(list_of_questions)

# <HINT> Create an exam result view to check if learner passed exam and show their question results and result for each question,
# you may implement it based on the following logic:
        # Get course and submission based on their ids
        # Get the selected choice ids from the submission record
        # For each selected choice, check if it is a correct answer or not
        # Calculate the total score
#def show_exam_result(request, course_id, submission_id):
def show_exam_result(request, course_id, submission_id):
    context = {}
    course = Course.objects.get(pk=course_id)
    submission = Submission.objects.get(pk=submission_id)
    number_of_questionsss = get_quest_number(course_id)
    selected_choice_ids = submission.chocies.all()
    total_score = 0
    print('im here')
    questions = []
    for id in selected_choice_ids:
        choice = Choice.objects.get(pk=id.pk)
        question = choice.question_id
        if question_exist(questions, question.pk) == False:
            print('question added:')
            print(question)
            print('to')
            print(questions)
            print('exist=')
            print(question_exist(questions, question))
            questions.append(question.id)
    print('the questions of the exam:')
    print(questions)
    number_of_questions = len(questions)
    print(number_of_questions)
    selected_correct_choices = []
    correct_and_not_selected = []
    questions_total_score = 0
    for question in questions:
        number_of_correct_answers = 0
        question_score = 0
        print('number of correct answers')
        print(number_of_correct_choices(question))
        choices = Choice.objects.filter(question_id=question)
        for choice in choices:
            if choice.is_correct:
                if choice_is_selected(choice, submission_id):              
                    number_of_correct_answers += 1
                    question_score += 1
                    selected_correct_choices.append(choice.pk)
                else: 
                    correct_and_not_selected.append(choice.pk)
            if not choice.is_correct:
                if choice_is_selected(choice, submission_id):              
                    number_of_correct_answers -= 1
                    question_score -= 1
        if question_score < 0:
            question_score = 0
        if number_of_correct_answers < 0:
            number_of_correct_answers = 0
        questions_total_score += question_score
        total_score += (number_of_correct_answers/number_of_correct_choices(question))
        print('number of correct answers and then correct choices')
        print(number_of_correct_answers)
        print(number_of_correct_choices(question))
    print('total score')
    print(total_score)
    total_score = int((total_score * 100)/number_of_questionsss)

    #for id in selected_choice_ids:
        #print(id.pk)
        #int(''.join(filter(str.isdigit, id))) 
        #id = int(id)
        #choice = Choice.objects.get(pk=id.pk)
        #if choice.is_correct:
            #total_score += 1
    selected_choice_idss = []
    for id in selected_choice_ids:
        selected_choice_idss.append(id.pk)
    print(selected_correct_choices)
    print(selected_correct_choices.count(1))
    print('selected_choice_idss')
    print(selected_choice_idss)
    print('number of questionsss')
    print(number_of_questionsss)
    context['course'] = course
    context['submission'] = submission
    context['selected_choice_idss'] = selected_choice_idss
    context['total_score'] = total_score
    context['selected_correct_choices'] = selected_correct_choices 
    context['correct_and_not_selected'] = correct_and_not_selected

    return render(request, 'onlinecourse/exam_result_bootstrap.html', context)
   
