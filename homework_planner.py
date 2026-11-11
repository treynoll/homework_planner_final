from dataclasses import dataclass
from datetime import date
from drafter import *
from bakery import assert_equal

@dataclass
class Assignment:
    """Store the information for one homework assignment."""
    assignment_name: str
    course_name: str
    due_date: str
    completed: bool


@dataclass
class Course:
    """Store the name of one course in the planner."""
    course_name: str


@dataclass
class State:
    """Store all information that the website needs between pages."""
    assignments: list[Assignment]
    courses: list[Course]
    student_name: str
    selected_course: str
    show_completed: bool


def course_names(state: State) -> list[str]:
    """Return the course names as strings for a dropdown menu."""
    names = []
    for course in state.courses:
        names.append(course.course_name)
    return names


def add_navigation(content: list) -> list:
    """Add the website navigation buttons to a page."""
    content.append("\n")
    content.append(Button("Home", "home_page"))
    content.append(Button("Add Assignment", "add_assignment"))
    content.append(Button("All Assignments", "all_assignments"))
    content.append(Button("Completed", "completed_assignments"))
    content.append(Button("Overdue", "overdue_assignments"))
    content.append(Button("Courses", "courses_page"))
    content.append(Button("Progress", "progress_page"))
    content.append("\n")
    return content


def is_valid_date(date_text: str) -> bool:
    """Check whether a date is entered in YYYY-MM-DD format."""
    try:
        date.fromisoformat(date_text)
        return True
    except ValueError:
        return False


def assignment_description(assignment: Assignment) -> str:
    """Create a readable description of an assignment."""
    if assignment.completed:
        status = "Completed"
    elif assignment.due_date < date.today().isoformat():
        status = "OVERDUE"
    else:
        status = "Not completed"

    return (assignment.assignment_name + " | " +
            assignment.course_name + " | Due: " +
            assignment.due_date + " | " + status)


@route
def index(state: State) -> Page:
    """Open the website at the home page."""
    return home_page(state)


@route
def home_page(state: State) -> Page:
    """Display the home page and a short summary of the student's work."""
    total = len(state.assignments)
    completed_count = 0
    overdue_count = 0

    for assignment in state.assignments:
        if assignment.completed:
            completed_count = completed_count + 1
        elif assignment.due_date < date.today().isoformat():
            overdue_count = overdue_count + 1

    content = [
        Header("🎓Homework Planner"),
        "Welcome, " + state.student_name + "!",
        "\nKeep track of your assignments, courses, and due dates.",
        "\n", "Last selected course: " + state.selected_course,
        "Total assignments: " + str(total),
        "\nCompleted assignments: " + str(completed_count),
        "\nOverdue assignments: " + str(overdue_count),
        "\n"
    ]
    add_navigation(content)
    content.extend([
    "Change your name:",
    TextBox("student_name"),
    Button("Update Name", "update_student_name")
])
    content.append(Header("📅Upcoming work"))

    found_upcoming = False
    for assignment in state.assignments:
        if not assignment.completed and assignment.due_date >= date.today().isoformat():
            content.append(assignment_description(assignment))
            content.append("\n")
            found_upcoming = True

    if not found_upcoming:
        content.append("You have no upcoming assignments.")

    return Page(state, content)


@route
def add_assignment(state: State) -> Page:
    """Show a form where the student can enter a new assignment."""
    names = course_names(state)
    content = [Header("Add an Assignment")]
    add_navigation(content)

    if len(names) == 0:
        content.append("Please add a course before adding an assignment.")
        content.append(Button("Go to Courses", "courses_page"))
        return Page(state, content)

    content.extend([
        "Assignment name:",
        TextBox("assignment_name"),
        "\nCourse:",
        SelectBox("course_name", names),
        "\nDue date (YYYY-MM-DD):",
        TextBox("due_date", date.today().isoformat()),
        "\nAlready completed?",
        CheckBox("completed"),
        "\n",
        Button("Save Assignment", "save_assignment")
    ])
    return Page(state, content)


@route
def save_assignment(state: State, assignment_name: str,
                    course_name: str, due_date: str,
                    completed: bool) -> Page:
    """Validate and save the assignment entered by the student."""
    if assignment_name.strip() == "":
        content = [Header("Missing Assignment Name"),
                   "Please enter an assignment name.",
                   Button("Go Back", "add_assignment")]
        return Page(state, content)

    if not is_valid_date(due_date):
        content = [Header("Date Format Error"),
                   "Enter the due date as YYYY-MM-DD, for example 2026-11-20.",
                   Button("Try Again", "add_assignment")]
        return Page(state, content)

    new_assignment = Assignment(
        assignment_name.strip(), course_name, due_date, completed
    )
    state.assignments.append(new_assignment)
    state.selected_course = course_name
    return home_page(state)


@route
def all_assignments(state: State) -> Page:
    """Display every assignment and allow unfinished work to be completed."""
    content = [Header("All Assignments")]
    add_navigation(content)

    if len(state.assignments) == 0:
        content.append("You have not added any assignments yet.")
    else:
        for index in range(len(state.assignments)):
            assignment = state.assignments[index]
            content.append(assignment_description(assignment))
            content.append("\n")
            if not assignment.completed:
                content.append(Button(
                    "Mark Completed",
                    "mark_completed",
                    [Argument("assignment_index", index)]
                ))
                content.append("\n")

    return Page(state, content)


@route
def mark_completed(state: State, assignment_index: int) -> Page:
    """Mark the selected assignment as completed."""
    if 0 <= assignment_index < len(state.assignments):
        state.assignments[assignment_index].completed = True
    return all_assignments(state)


@route
def completed_assignments(state: State) -> Page:
    """Show only assignments that have been marked completed."""
    content = [Header("✅Completed Assignments")]
    add_navigation(content)

    found_completed = False
    for assignment in state.assignments:
        if assignment.completed:
            content.append(assignment_description(assignment))
            content.append("\n")
            found_completed = True

    if not found_completed:
        content.append("No completed assignments yet.")

    return Page(state, content)


@route
def overdue_assignments(state: State) -> Page:
    """Show unfinished assignments whose due dates have passed."""
    content = [Header("Overdue Assignments")]
    add_navigation(content)

    found_overdue = False
    today = date.today().isoformat()

    for assignment in state.assignments:
        if not assignment.completed and assignment.due_date < today:
            content.append(assignment_description(assignment))
            content.append("\n")
            found_overdue = True

    if not found_overdue:
        content.append("You have no overdue assignments.")

    return Page(state, content)


@route
def courses_page(state: State) -> Page:
    """Display the courses and provide a form to add another course."""
    content = [Header("My Courses")]
    add_navigation(content)
    content.append("Courses in your planner:\n")

    if len(state.courses) == 0:
        content.append("No courses have been added.")
    else:
        for course in state.courses:
            content.append("- " + course.course_name + "\n")

    content.extend([
        "\nAdd a course:",
        TextBox("new_course_name"),
        "\n",
        Button("Add Course", "add_course")
    ])
    return Page(state, content)


@route
def add_course(state: State, new_course_name: str) -> Page:
    """Add a new course if its name is not blank or already listed."""
    cleaned_name = new_course_name.strip()

    if cleaned_name != "":
        already_exists = False
        for course in state.courses:
            if course.course_name.lower() == cleaned_name.lower():
                already_exists = True

        if not already_exists:
            state.courses.append(Course(cleaned_name))

    return courses_page(state)


@route
def progress_page(state: State) -> Page:
    """Calculate and display the student's assignment completion progress."""
    total = len(state.assignments)
    completed_count = 0

    for assignment in state.assignments:
        if assignment.completed:
            completed_count = completed_count + 1

    if total == 0:
        percentage = 0
    else:
        percentage = round(completed_count / total * 100)

    content = [
        Header("My Progress"),
        "Completed assignments: " + str(completed_count),
        "\nTotal assignments: " + str(total),
        "\nCompletion: " + str(percentage) + "%",
        "\n"
    ]
    add_navigation(content)
    return Page(state, content)

@route
def update_student_name(state: State, student_name: str) -> Page:
    """Update the student's name on the home page."""
    cleaned_name = student_name.strip()

    if cleaned_name != "":
        state.student_name = cleaned_name

    return home_page(state)

# Test course_names
test_state = State(
    assignments=[],
    courses=[Course("CISC106"), Course("Math")],
    student_name="Student",
    selected_course="CISC106",
    show_completed=False
)

assert_equal(course_names(test_state), ["CISC106", "Math"])


# Test valid dates
assert_equal(is_valid_date("2026-11-20"), True)
assert_equal(is_valid_date("11/20/2026"), False)
assert_equal(is_valid_date("2026-15-20"), False)


# Test completed assignments
test_assignment = Assignment(
    "Homework 1", "CISC106", "2026-11-20", True
)

assert_equal(
    assignment_description(test_assignment),
    "Homework 1 | CISC106 | Due: 2026-11-20 | Completed"
)


# Test unfinished future assignments
test_assignment2 = Assignment(
    "Homework 2",
    "Math",
    "2099-12-20",
    False
)

assert_equal(
    assignment_description(test_assignment2),
    "Homework 2 | Math | Due: 2099-12-20 | Not completed"
)
# The initial state includes a few example courses.
# The student can add or change courses from the Courses page.
'''Used the if statement to make sure the server is ran after the unit test'''
if __name__ == "__main__":
    start_server(
        State(
            assignments=[],
            courses=[
                Course("CISC106"),
                Course("Math"),
                Course("Chemistry")
            ],
            student_name="Student",
            selected_course="CISC106",
            show_completed=False
        ),
        port=8001,
        site_title="Homework Planner"
    )