"""wounderland.prompt.scratch"""

import random
import datetime
from jinja2 import Template
from wounderland import utils
from wounderland.memory import Event
from wounderland.model import parse_llm_output


class Scratch:
    def __init__(self, name, currently, config):
        self.name = name
        self.currently = currently
        self.config = config

    def _base_desc(self):
        return """Name: {0}
Age: {1}
Innate traits: {2}
Learned traits: {3}
Currently: {4}
Lifestyle: {5}
Daily plan requirement: {6}
Current Date: {7}\n""".format(
            self.name,
            self.config["age"],
            self.config["innate"],
            self.config["learned"],
            self.currently,
            self.config["lifestyle"],
            self.config["daily_plan"],
            utils.get_timer().daily_format(),
        )

    def _format_output(self, prompt, style, example="", instruction=""):
        prompt = '"""\n' + prompt + '\n"""\n'
        prompt += f"Output the response to the prompt above in {style}."
        if instruction:
            prompt += f" {instruction}"
        if example:
            prompt += f"\nExample output {style}:\n{example}"
        return prompt

    def prompt_poignancy_event(self, event):
        prompt = self._base_desc()
        prompt += f"""\nOn the scale of 1 to 10, where 1 is purely mundane (e.g., regular medical affairs, Routine inspection) and 10 is extremely poignant (e.g., first aid, major surgery), rate the likely poignancy of the following event for {self.name}.
Each event should ONLY be rate with ONE integer on the scale of 1 to 10.
-----
Event: Daily medical affairs. Rate: 1
-----
Event: Minor medical condition. Rate: 4
-----
Event: Important medical event. Rate: 7
-----
Event: Emergency or critical medical event. Rate: 10
-----
Event: {event.get_describe()}. Rate: """

        def _callback(response):
            pattern = ["Event: .*\. Rate: (\d{1,2})", "Rate: (\d{1,2})"]
            return int(parse_llm_output(response, pattern, "match_last"))

        return {
            "prompt": prompt,
            "callback": _callback,
            "failsafe": random.choice(list(range(10))) + 1,
        }

    def prompt_poignancy_chat(self, event):
        prompt = self._base_desc()
        prompt += f"""\nOn the scale of 1 to 10, where 1 is purely mundane (e.g., routine inspection) and 10 is extremely poignant (e.g., more serious infection, a major surgery), rate the likely poignancy of the following conversation for {self.name}.
Each Conversation should ONLY be rate with ONE integer on the scale of 1 to 10.
-----
Conversation: daily medical conversations. Rate: 1
-----
Conversation: minor medical condition. Rate: 4
-----
Conversation: key medical conversations. Rate: 8
-----
Conversation: emergency or critical medical conversations. Rate: 10
-----
Conversation: {event.get_describe()}. Rate: """

        def _callback(response):
            pattern = "Conversation: .*\. Rate: (\d{1,2})"
            return int(parse_llm_output(response, pattern, "match_last"))

        return {
            "prompt": prompt,
            "callback": _callback,
            "failsafe": random.choice(list(range(10))) + 1,
        }

    def prompt_wake_up(self):
        prompt = self._base_desc()
        prompt += """\nIn general, {}\n{}'s wake up hour:""".format(
            self.config["lifestyle"], self.name
        )
        prompt = self._format_output(
            prompt, "hour", "8:00 am", "The output should ONLY contain ONE hour value."
        )

        def _callback(response):
            return int(parse_llm_output(response, ["(\d):00 am+", "(\d) am+"]))

        return {"prompt": prompt, "callback": _callback, "failsafe": 6}

    def prompt_schedule_init(self, wake_up):
        prompt = self._base_desc()
        prompt += """\nIn general, {}""".format(self.config["lifestyle"])
        prompt += "\nToday is {}. Here is {}'s plan today in broad-strokes ".format(
            utils.get_timer().daily_format(), self.name
        )
        prompt += "(with the time of the day. e.g., eat breakfast at 7:00 AM, have a lunch at 12:00 PM, watch TV at 7:00 PM):\n"
        prompt += (
            "1) wake up and complete the morning routine at {}:00 AM.\n2) ".format(
                wake_up
            )
        )
        prompt = self._format_output(
            prompt, "lines", instruction="Each line consist of index and plan"
        )

        def _callback(response):
            patterns = ["\d{1,2}\) (.*)\.", "\d{1,2}\) (.*)", "(.*)\.", "(.*)"]
            return parse_llm_output(response, patterns, mode="match_all")

        failsafe = [
            "Wake up and complete the morning routine at 6:00 AM",
            "eat breakfast at 7:00 AM",
            "Review patient files and the latest medical research at 8:00 AM",
            "Drive to the hospital and check in at the front desk at 9:00 AM",
            "Conduct ward rounds to visit in - patients at 9:30 AM",
            "Have a working lunch in the hospital cafeteria at 12:00 PM",
            "Start outpatient consultations in the clinic at 2:00 PM.",
            "Attend a meeting with the nursing staff at 3:00 PM",
            "Review the latest medical research and prepare for the next day's rounds at 5:00 PM",
            "Drive home and prepare for the evening at 6:00 PM",
            "Relax and watch TV at 7:00 PM",
            "Go to bed at 10:00 PM",
        ]
        return {"prompt": prompt, "callback": _callback, "failsafe": failsafe}

    def prompt_schedule_daily(self, wake_up, schedule, daily_schedule):
        prompt = "Hourly schedule format:\n"
        for hour, _ in schedule:
            prompt += f"[{hour}] Activity: [Fill in]\n"
        prompt += "========\n"
        prompt += self._base_desc()
        prompt += "\nHere the originally intended hourly breakdown of {}'s schedule today:\n".format(
            self.name
        )
        prompt += "; ".join(daily_schedule)
        prompt += "\n\n" + "\n".join(
            [
                "[{}] Activity: {} is {}".format(h, self.name, s)
                for h, s in schedule[: wake_up + 1]
            ]
        )

        failsafe = {
            "6:00 AM": "Wake up, wash up, and do a simple stretch",
            "7:00 AM": "Have a nutritious breakfast",
            "8:00 AM": "Review patient medical records",
            "9:00 AM": "Study cutting - edge medical research",
            "10:00 AM": "Attend pre - operation discussions",
            "11:00 AM": "Prepare surgical instruments",
            "12:00 PM": "Have a quick meal in the hospital cafeteria",
            "1:00 PM": "Take a short nap in the on - call room",
            "2:00 PM": "Continue napping",
            "3:00 PM": "Get up, move around, and wake up",
            "4:00 PM": "Conduct patient consultations",
            "5:00 PM": "Discuss cases with colleagues",
            "6:00 PM": "Go home after work",
            "7:00 PM": "Relax by watching medical documentaries",
            "8:00 PM": "Continue watching educational programs",
            "9:00 PM": "Read medical journals before bedtime",
            "10:00 PM": "Do breathing relaxation exercises and prepare to sleep",
            "11:00 PM": "Fall asleep"
        }

        def _callback(response):
            patterns = [
                "\[(\d{1,2}:\d{2} AM)\] Activity: " + self.name + " is (.*)\.",
                "\[(\d{1,2}:\d{2} AM)\] Activity: " + self.name + " is (.*)",
                "\[(\d{1,2}:\d{2} PM)\] Activity: " + self.name + " is (.*)\.",
                "\[(\d{1,2}:\d{2} PM)\] Activity: " + self.name + " is (.*)",
                "\[(\d{1,2}:\d{2} AM)\] Activity: " + self.name + " (.*)\.",
                "\[(\d{1,2}:\d{2} AM)\] Activity: " + self.name + " (.*)",
                "\[(\d{1,2}:\d{2} PM)\] Activity: " + self.name + " (.*)\.",
                "\[(\d{1,2}:\d{2} PM)\] Activity: " + self.name + " (.*)",
            ]
            outputs = parse_llm_output(response, patterns, mode="match_all")
            assert len(outputs) >= 5, "less than 5 schedules"
            return {s[0]: s[1] for s in outputs}

        return {"prompt": prompt, "callback": _callback, "failsafe": failsafe}

    def prompt_schedule_decompose(self, plan, schedule):
        def _plan_des(plan):
            start, end = schedule.plan_stamps(plan, time_format="%H:%M%p")
            return f'{start} ~ {end}, {self.name} is planning on {plan["describe"]}'

        prompt = """Describe subtasks in 5 min increments.
[Examples]
Name: Isabella Rodriguez
Age: 45
Backstory: rodriguez has always been passionate about surgery and has become a renowned surgeon in the field. During the week, she dedicates himself to his patients and research, but on the weekends, she enjoys playing golf and spending time with his family. She is highly skilled, focused, and compassionate.
Personality: skilled, focused, compassionate
Location: rodriguez is in a modern hospital that has the following areas: {operating room, office, cafeteria, lounge, patient rooms, research lab}.
Currently: rodriguez is a surgeon who performs surgeries and conducts medical research. She is currently working at a leading hospital.
Daily plan requirement: rodriguez is planning to perform surgeries in the morning and conduct research in the afternoon.
Today is Monday, January 15. From 07:00AM ~ 09:00AM, rodriguez is planning on performing a complex surgery, from 09:00AM ~ 11:00AM, rodriguez is planning on consulting with patients, and from 11:00AM ~ 1:00PM, rodriguez is planning on conducting research.
In 5 min increments, list the subtasks rodriguez does when she is performing a complex surgery from 07:00AM ~ 09:00AM (total duration in minutes: 120):

<subtasks>:
1) rodriguez <is> reviewing the patient's medical history. (duration: 15, left: 105)
2) rodriguez <is> preparing the surgical instruments. (duration: 20, left: 85)
3) rodriguez <is> performing the initial incision. (duration: 30, left: 55)
4) rodriguez <is> conducting the main procedure. (duration: 40, left: 15)
5) rodriguez <is> closing the incision and finishing the surgery. (duration: 15, left: 0)

Name: Klaus Mueller
Age: 50
Backstory: Klaus Mueller has always been fascinated by medical imaging and has become a renowned radiologist in the field. During the week, he dedicates himself to his patients and research, but on the weekends, he enjoys hiking and spending time with his family. He is highly analytical, detail-oriented, and compassionate.
Personality: analytical, detail-oriented, compassionate
Location: Klaus is in a state-of-the-art hospital that has the following areas: {radiology department, office, cafeteria, lounge, patient rooms, research lab}.
Currently: Klaus is a radiologist who interprets medical images and conducts research in radiology. He is currently working at a leading hospital.
Daily plan requirement: Klaus is planning to review imaging scans in the morning and conduct research in the afternoon.
Today is Monday, January 15. From 07:00AM ~ 09:00AM, Klaus is planning on reviewing complex imaging scans, from 09:00AM ~ 11:00AM, Klaus is planning on consulting with referring physicians, and from 11:00AM ~ 1:00PM, Klaus is planning on conducting research.
In 5 min increments, list the subtasks Klaus does when he is reviewing complex imaging scans from 07:00AM ~ 09:00AM (total duration in minutes: 120):
 
<subtasks>:
1) Klaus <is> reviewing the patient's medical history and previous scans. (duration: 15, left: 105)
2) Klaus <is> analyzing the new imaging scans. (duration: 30, left: 75)
3) Klaus <is> comparing new scans with previous results. (duration: 20, left: 55)
4) Klaus <is> discussing findings with the radiology team. (duration: 30, left: 25)
5) Klaus <is> preparing a detailed report for the referring physician. (duration: 25, left: 0)

Name: Maria Lopez
Age: 48
Backstory: Maria Lopez has always been dedicated to patient care and has become a renowned internist in the field. During the week, she dedicates herself to her patients and medical education, but on the weekends, she enjoys reading and spending time with her family. She is highly knowledgeable, empathetic, and thorough.
Personality: knowledgeable, empathetic, thorough
Location: Maria is in a well-equipped hospital that has the following areas: {consultation rooms, office, cafeteria, lounge, patient rooms, research lab}.
Currently: Maria is an internist who diagnoses and treats a wide range of internal diseases. She is currently working at a leading hospital.
Daily plan requirement: Maria is planning to see patients in the morning and conduct medical education sessions in the afternoon.
Today is Monday, January 15. From 07:00AM ~ 09:00AM, Maria is planning on conducting patient consultations, from 09:00AM ~ 11:00AM, Maria is planning on reviewing patient cases, and from 11:00AM ~ 1:00PM, Maria is planning on conducting a medical education session.
In 5 min increments, list the subtasks Maria does when she is conducting patient consultations from 07:00AM ~ 09:00AM (total duration in minutes: 120):

<subtasks>:
1) Maria <is> reviewing the patient's medical history. (duration: 15, left: 105)
2) Maria <is> conducting a physical examination. (duration: 30, left: 75)
3) Maria <is> discussing symptoms and concerns with the patient. (duration: 20, left: 55)
4) Maria <is> formulating a diagnosis and treatment plan. (duration: 30, left: 25)
5) Maria <is> documenting the consultation and updating medical records. (duration: 25, left: 0)

Given example above, please list the subtasks of the following task.
[TASK]\n"""
        prompt += self._base_desc()
        indices = range(
            max(plan["idx"] - 1, 0), min(plan["idx"] + 2, len(schedule.daily_schedule))
        )
        prompt += f"\nToday is {utils.get_timer().daily_format()}. From "
        prompt += ", ".join([_plan_des(schedule.daily_schedule[i]) for i in indices])
        start, end = schedule.plan_stamps(plan, time_format="%H:%M%p")
        increment = max(int(plan["duration"] / 100) * 5, 5)
        prompt += f'\nIn {increment} min increments, list the subtasks {self.name} does when {self.name} is {plan["describe"]}'
        prompt += (
            f' from {start} ~ {end} (total duration in minutes {plan["duration"]}):\n\n'
        )
        prompt += "<subtasks>:\n"
        prompt += f"1) {self.name} <is> "

        def _callback(response):
            patterns = [
                "\d{1,2}\) .* <is> (.*) \(duration: (\d{1,2}), left: \d*\)",
                ".* <is> (.*) \(duration: (\d{1,2}), left: \d*\)",
            ]
            schedules = parse_llm_output(response, patterns, mode="match_all")
            schedules = [(s[0].strip("."), int(s[1])) for s in schedules]
            left = plan["duration"] - sum([s[1] for s in schedules])
            if left > 0:
                schedules.append((plan["describe"], left))
            return schedules

        failsafe = [(plan["describe"], 10) for _ in range(int(plan["duration"] / 10))]
        return {"prompt": prompt, "callback": _callback, "failsafe": failsafe}

    def prompt_schedule_revise(self, action, schedule):
        plan, _ = schedule.current_plan()
        start, end = schedule.plan_stamps(plan, time_format="%H:%M")
        act_start_minutes = utils.daily_duration(action.start)
        org_plan, new_plan = [], []

        def _plan_des(start, end, describe):
            if not isinstance(start, str):
                start = start.strftime("%H:%M")
            if not isinstance(end, str):
                end = end.strftime("%H:%M")
            return "[{} ~ {}] {} ({})".format(start, end, plan["describe"], describe)

        for de_plan in plan["decompose"]:
            de_start, de_end = schedule.plan_stamps(de_plan, time_format="%H:%M")
            org_plan.append(_plan_des(de_start, de_end, de_plan["describe"]))
            if de_plan["start"] + de_plan["duration"] <= act_start_minutes:
                new_plan.append(_plan_des(de_start, de_end, de_plan["describe"]))
            elif de_plan["start"] <= act_start_minutes:
                new_plan.extend(
                    [
                        _plan_des(de_start, action.start, de_plan["describe"]),
                        _plan_des(
                            action.start, action.end, action.event.get_describe(False)
                        ),
                    ]
                )
                new_plan.append("[{} ~".format(action.end.strftime("%H:%M")))

        org_plan, new_plan = "\n".join(org_plan), "\n".join(new_plan)
        prompt = f"""Here was {self.name}'s originally planned schedule from {start} to {end}. 
{org_plan}\n
But {self.name} unexpectedly end up with the following event for {action.duration} minutes:\n{action.event.get_describe()}.
\nRevise {self.name}'s schedule from {start} to {end} accordingly (it has to end by {end}). 
The revised schedule:
{new_plan}"""

        def _callback(response):
            patterns = [
                "^\[(\d{1,2}:\d{1,2}) ~ (\d{1,2}:\d{1,2})\] continuing to work at the counter \((.*)\)",
                "^\[(\d{1,2}:\d{1,2}) ~ (\d{1,2}:\d{1,2})\] (.*)",
            ]
            schedules = parse_llm_output(response, patterns, mode="match_all")
            decompose = []
            for start, end, describe in schedules:
                m_start = utils.daily_duration(utils.to_date(start, "%H:%M"))
                m_end = utils.daily_duration(utils.to_date(end, "%H:%M"))
                decompose.append(
                    {
                        "idx": len(decompose),
                        "describe": describe,
                        "start": m_start,
                        "duration": m_end - m_start,
                    }
                )
            return decompose

        return {"prompt": prompt, "callback": _callback, "failsafe": plan["decompose"]}

    def prompt_determine_sector(self, describes, spatial, address, tile):
        template = Template(
            """\n-----
{{ name }} lives in <{{ live_sector }}> that has {{ live_arenas|join(', ') }}.
{{ name }} is currently in <{{ curr_sector }}> that has {{ curr_arenas|join(', ') }}.
{{ daily_plan }}
Area options: <{{ areas|join(', ') }}>.
* Stay in the current area if the activity can be done there. Only go out if the activity needs to take place in another place.
* Must be one of the "Area options", verbatim.
{{ name }} is {{ describes[0] }}. For {{ describes[1] }}, {{ name }} should go to the following area: {% if answer %}<{{ answer }}>{% else %}<{% endif %}"""
        )

        prompt = "Task -- choose an appropriate area from the area options for a task at hand."
        prompt += template.render(
            name="Klaus Mueller",
            live_sector="City Hospital",
            live_arenas=["Radiology Department", "Office", "Cafeteria"],
            curr_sector="City Hospital",
            curr_arenas=["Radiology Department", "Office", "Cafeteria"],
            daily_plan="Klaus Mueller reviews imaging scans and conducts research.",
            areas=[
                "City Hospital",
                "Central Park",
                "Downtown Cafe",
                "Medical Research Institute",
                "Community Health Center",
                "Pharmacy",
                "Library",
            ],
            describes=["analyzing scans", "conducting research"],
            answer="Radiology Department",
        )
        prompt += template.render(
            name="Maria Lopez",
            live_sector="General Hospital",
            live_arenas=["Consultation Rooms", "Office", "Cafeteria"],
            curr_sector="General Hospital",
            curr_arenas=["Consultation Rooms", "Office", "Cafeteria"],
            daily_plan="Maria Lopez sees patients and conducts medical education sessions.",
            areas=[
                "General Hospital",
                "City Park",
                "Downtown Bistro",
                "Medical School",
                "Community Clinic",
                "Pharmacy",
                "Public Library",
            ],
            describes=["consulting patients", "teaching medical students"],
            answer="Consultation Rooms",
        )
        live_address = spatial.find_address("living_area", as_list=True)[:-1]
        curr_address = tile.get_address("sector", as_list=True)
        prompt += template.render(
            name=self.name,
            live_sector=live_address[-1],
            live_arenas=spatial.get_leaves(live_address),
            curr_sector=curr_address[-1],
            curr_arenas=spatial.get_leaves(curr_address),
            daily_plan=self.config["daily_plan"],
            areas=spatial.get_leaves(address),
            describes=describes,
        )

        sectors = spatial.get_leaves(address)
        arenas = {}
        for sec in sectors:
            arenas.update(
                {a: sec for a in spatial.get_leaves(address + [sec]) if a not in arenas}
            )
        failsafe = random.choice(sectors)

        def _callback(response):
            pattern = self.name + " .* area: <(.+?)>"
            sector = parse_llm_output(response, pattern)
            if sector in sectors:
                return sector
            if sector in arenas:
                return arenas[sector]
            for s in sectors:
                if sector.startswith(s):
                    return s
            return failsafe

        return {"prompt": prompt, "callback": _callback, "failsafe": failsafe}

    def prompt_determine_arena(self, describes, spatial, address):
        template = Template(
            """\n-----
{{ name }} is going to {{ dst_sector }} that has the following areas: <{{ dst_arenas|join(', ') }}>.
{{ daily_plan }}
* Stay in the current area if the activity can be done there. Never go into other people's rooms unless necessary.
* Must be one of the given areas, verbatim.
{{ name }} is {{ describes[0] }}. For {{ describes[1] }}, {{ name }} should go to the following area in {{ dst_sector }}: {% if answer %}<{{ answer }}>{% else %}<{% endif %}"""
        )

        prompt = "Task -- choose an appropriate area from the areas for a task at hand."
        prompt += template.render(
            name="Klaus Mueller",
            dst_sector="City Hospital",
            dst_arenas=["Radiology Department", "Office", "Cafeteria"],
            daily_plan="Klaus Mueller reviews imaging scans and conducts research.",
            describes=["analyzing scans", "conducting research"],
            answer="Radiology Department",
        )
        prompt += template.render(
            name="Tom Watson",
            dst_sector="Hobbs Cafe",
            dst_arenas=["cafe"],
            daily_plan="Tom Watson visit cafe around 8am and go to campus for classes.",
            describes=["eating breakfast", "getting coffee"],
            answer="cafe",
        )
        prompt += template.render(
            name=self.name,
            dst_sector=address[-1],
            dst_arenas=spatial.get_leaves(address),
            daily_plan=self.config["daily_plan"],
            describes=describes,
        )

        arenas = spatial.get_leaves(address)
        failsafe = random.choice(arenas)

        def _callback(response):
            pattern = (
                    self.name
                    + " should go to the following area in "
                    + address[-1]
                    + ": <(.+?)>"
            )
            arena = parse_llm_output(response, pattern)
            return arena if arena in arenas else failsafe

        return {"prompt": prompt, "callback": _callback, "failsafe": failsafe}

    def prompt_determine_object(self, describes, spatial, address):
        template = Template(
            """\n-----
Current activity: {{ activity }}
Objects: <{{ objects|join(', ') }}>
The most relevant object from the Objects is: {% if answer %}<{{ answer }}>{% else %}<{% endif %}"""
        )

        prompt = "Task -- choose most relevant object from the Objects for a task at hand.\n[Examples]"
        prompt += template.render(
            activity="review patient records",
            objects=["computer", "patient file", "desk", "chair"],
            answer="patient file",
        )
        prompt += template.render(
            activity="conduct a medical examination",
            objects=["stethoscope", "examination table", "blood pressure cuff", "thermometer"],
            answer="examination table",
        )
        prompt += template.render(
            activity="conduct a medical examination",
            objects=["stethoscope", "examination table", "blood pressure cuff", "thermometer"],
            answer="examination table",
        )
        prompt += template.render(
            activity="perform surgery",
            objects=["scalpel", "surgical table", "anesthesia machine", "surgical lights"],
            answer="surgical table",
        )
        prompt += template.render(
            activity="analyze imaging scans",
            objects=["computer", "MRI machine", "X-ray viewer", "desk"],
            answer="MRI machine",
        )
        prompt += template.render(
            activity="attend a medical seminar",
            objects=["projector", "lecture notes", "conference room", "microphone"],
            answer="conference room",
        )
        prompt += template.render(
            activity="consult with a patient",
            objects=["consultation room", "patient chair", "doctor's chair", "medical chart"],
            answer="consultation room",
        )

        objects = spatial.get_leaves(address)
        failsafe = random.choice(objects)

        def _callback(response):
            pattern = "The most relevant object from the Objects is: <(.+?)>"
            obj = parse_llm_output(response, pattern)
            return obj if obj in objects else failsafe

        return {"prompt": prompt, "callback": _callback, "failsafe": failsafe}

    def prompt_describe_emoji(self, describe):
        prompt = f"""Convert an action description to an emoji (important: use three or less emojis).\n
[Examples]
Action description: reviewing patient records (checking the latest test results)
Emoji: 📄🩺
Action description: conducting a medical examination (using a stethoscope)
Emoji: 🩺👩‍⚕️
Action description: performing surgery (preparing the surgical instruments)
Emoji: 🏥🔪
Action description: consulting with a patient (discussing treatment options)
Emoji: 🗣️💊
Action description: attending a medical seminar (taking notes)
Emoji: 📝📚

Given the examples above, please convert the following action to an emoji (important: use three or less emojis):
Action description: {describe}
Emoji: """

        def _callback(response):
            output = parse_llm_output(response, "Emoji: (.*)")[:3] or "🦁"
            return output.replace(" ", "")

        return {"prompt": prompt, "callback": _callback, "failsafe": "🦁", "retry": 1}

    def prompt_describe_event(self, subject, describe, address, emoji=None):
        prompt = f"""Task: Turn the input into format (<subject>, <predicate>, <object>).\n
[Examples]
Input: Dr. Emily Carter is reviewing patient records.
Output: (<Dr. Emily Carter>, <review>, <patient records>)
---
Input: Dr. John Smith is conducting a physical examination.
Output: (<Dr. John Smith>, <conduct>, <physical examination>)
---
Input: Dr. Sarah Lee is performing surgery.
Output: (<Dr. Sarah Lee>, <perform>, <surgery>)
---
Input: Dr. David Brown is consulting with a patient.
Output: (<Dr. David Brown>, <consult>, <patient>)
---
Input: Dr. Linda Green is attending a medical seminar.
Output: (<Dr. Linda Green>, <attend>, <medical seminar>)
---
Input: Dr. Robert White is analyzing imaging scans.
Output: (<Dr. Robert White>, <analyze>, <imaging scans>)
---
Input: {describe}.
Output: (<"""

        e_describe = describe
        if e_describe.startswith(subject + " is "):
            e_describe = e_describe.replace(subject + " is ", "")
        failsafe = Event(
            subject, "is", e_describe, describe=describe, address=address, emoji=emoji
        )

        def _callback(response):
            patterns = [
                "\(<(.+?)>, <(.+?)>, <(.*)>\)\,",
                "\(<(.+?)>, <(.+?)>, <(.*)>\)",
                "\((.+?), (.+?), (.*)\)",
            ]
            outputs = parse_llm_output(response, patterns)
            if not outputs[2]:
                return failsafe
            return Event(*outputs, describe=describe, address=address, emoji=emoji)

        return {"prompt": prompt, "callback": _callback, "failsafe": failsafe}

    def prompt_describe_object(self, obj, describe):
        prompt = f"""Task: We want to understand the state of an object that is being used by someone.\n
[Examples]
Let's think step by step to know about stethoscope's state:
Step 1. Dr. Emily Carter is conducting a physical examination using the stethoscope.
Step 2. Describe the stethoscope's state: stethoscope is being used to listen to the patient's heartbeat
---
Let's think step by step to know about MRI machine's state:
Step 1. Dr. John Smith is analyzing imaging scans using the MRI machine.
Step 2. Describe the MRI machine's state: MRI machine is actively scanning and processing images
---
Let's think step by step to know about surgical table's state:
Step 1. Dr. Sarah Lee is performing surgery using the surgical table.
Step 2. Describe the surgical table's state: surgical table is occupied and in use for the procedure
---

Given the examples above, let's think step by step to know about {obj}'s state:
Step 1. {self.name} is {describe} at/using the {obj}.
Step 2. Describe the {obj}'s state: {obj} is """

        def _callback(response):
            patterns = [
                "Describe the " + obj + "'s state: " + obj + " is (.*)\.",
                "Describe the " + obj + "'s state: " + obj + " is (.*)\.",
                "Describe the " + obj + "'s state: .* is (.*)\.",
                "Describe the " + obj + "'s state: .* is (.*)",
            ]
            return parse_llm_output(response, patterns)

        return {"prompt": prompt, "callback": _callback, "failsafe": "idle"}

    def prompt_decide_chat(self, agent, other, focus, chats):
        def _status_des(agent):
            event = agent.get_event()
            if agent.path:
                return f"{agent.name} is on the way to {event.get_describe(False)}"
            return event.get_describe()

        context = ". ".join(
            [c.describe for c in focus["events"] if c.event.predicate == "was"]
        )
        context += "\n" + ". ".join([c.describe for c in focus["thoughts"]])
        date_str = utils.get_timer().get_date("%B %d, %Y, %H:%M:%S %p")
        chat_history = ""
        if chats:
            chat_history = f" {self.name} and {other.name} last chatted at {chats[0].create} about {chats[0].describe}"
        a_des, o_des = _status_des(agent), _status_des(other)
        prompt = f"""Task -- given context, determine whether the subject will initiate a conversation with another.
Context: {context}
Right now, it is {date_str}.{chat_history}
{a_des}\n{o_des}\n
Question: Would {self.name} initiate a conversation with {other.name}? \n
Answer in "yes" or "no":
"""

        # Reasoning: Let's think step by step.

        def _callback(response):
            return "yes" in response or "Yes" in response

        return {"prompt": prompt, "callback": _callback, "failsafe": False}

    def prompt_decide_wait(self, agent, other, focus):
        template = Template(
            """\n-----
Context: {{ context }}. 
Right now, it is {{ date }}. 
{{ status }}.
{{ name }} sees {{ o_status }}.
My question: Let's think step by step. Of the following two options, what should {{ name }} do?
Option 1: Wait on {{ action }} until {{ o_name }} is done {{ o_action }}
Option 2: Continue on to {{ action }} now
Reasoning: {{ reason }}
{% if answer %}Answer: <{{ answer }}>{% else %}{% endif %}
"""
        )

        prompt = "Task -- given context and two options that a subject can take, determine which option is the most acceptable.\n[Examples]\n"
        reason = """Dr. Emily and Dr. John both need to use the operating room. 
It would be impractical for both Dr. Emily and Dr. John to perform surgeries in the same operating room at the same time. 
So, since Dr. John is already using the operating room, the best option for Dr. Emily is to wait until the room is available."""
        prompt += template.render(
            context="Dr. Emily and Dr. John are colleagues at City Hospital. They discussed their surgery schedules during a morning meeting at 08:00 AM, January 15, 2023",
            date="09:00 AM, January 15, 2023",
            name="Dr. Emily",
            o_name="Dr. John",
            status="Dr. Emily is preparing for surgery",
            o_status="Dr. John is already performing surgery",
            action="performing surgery",
            o_action="performing surgery",
            reason=reason,
            answer="Option 1",
        )
        reason = """Dr. Sarah is likely going to be in the consultation room seeing patients. Dr. David, on the other hand, is likely headed to the radiology department to review scans.
Since Dr. Sarah and Dr. David need to use different areas, their actions do not conflict. 
So, since Dr. Sarah and Dr. David are going to be in different areas, Dr. Sarah can continue with her consultations now."""
        prompt += template.render(
            context="Dr. Sarah and Dr. David are colleagues at General Hospital. They exchanged a conversation about patient care at 10:00 AM, January 15, 2023",
            date="11:00 AM, January 15, 2023",
            name="Dr. Sarah",
            o_name="Dr. David",
            status="Dr. Sarah is on her way to see patients",
            o_status="Dr. David is heading to review scans",
            action="seeing patients",
            o_action="reviewing scans",
            reason=reason,
            answer="Option 2",
        )

        def _status_des(agent):
            event, loc = agent.get_event(), ""
            if event.address:
                loc = " at {} in {}".format(event.address[-1], event.address[-2])
            if not agent.path:
                return f"{agent.name} is already {event.get_describe(False)}{loc}"
            return f"{agent.name} is on the way to {event.get_describe(False)}{loc}"

        context = ". ".join(
            [c.describe for c in focus["events"] if c.event.predicate == "was"]
        )
        context += "\n" + ". ".join([c.describe for c in focus["thoughts"]])

        prompt += "\nGiven the examples above, determine which option is the most acceptable for the following task:"
        prompt += template.render(
            context=context,
            date=utils.get_timer().get_date("%B %d, %Y, %H:%M %p"),
            name=self.name,
            o_name=other.name,
            status=_status_des(agent),
            o_status=_status_des(other),
            action=agent.get_event().get_describe(False),
            o_action=other.get_event().get_describe(False),
        )

        def _callback(response):
            return "Option 1" in response

        return {"prompt": prompt, "callback": _callback, "failsafe": False}

    def prompt_summarize_relation(self, agent, other_name):
        nodes = agent.associate.retrieve_focus([other_name], 50)
        prompt = "[Statements]\n"
        prompt += "\n".join(
            ["{}. {}".format(idx, n.describe) for idx, n in enumerate(nodes)]
        )
        prompt += f"\n\nBased on the statements above, summarize {self.name} and {other_name}'s relationship (e.g., Tom and Jeo are friends, Elin and John are playing games). What do they feel or know about each other?\n"
        prompt = self._format_output(
            prompt,
            "sentence",
            "Jane and Tom are friends",
            "The output should be ONE sentence that describe the relationship.",
        )

        def _callback(response):
            return response

        return {
            "prompt": prompt,
            "callback": _callback,
            "failsafe": self.name + " is looking at " + other_name,
        }

    def prompt_generate_chat(self, agent, other, relation, chats):
        focus = [relation, other.get_event().get_describe()]
        if len(chats) > 4:
            focus.append("; ".join("{}: {}".format(n, t) for n, t in chats[-4:]))
        nodes = agent.associate.retrieve_focus(focus, 15)
        chat_nodes = agent.associate.retrieve_chats(other.name)
        pass_context = ""
        for n in chat_nodes:
            delta = utils.get_timer().get_delta(n.create)
            if delta > 480:
                continue
            pass_context += f"{delta} minutes ago, {agent.name} and {other.name} were already {n.describe}. This context takes place after that conversation.\n"

        address = agent.get_tile().get_address()
        curr_context = (
                f"{agent.name} "
                + f"was {agent.get_event().get_describe(False)} "
                + f"when {agent.name} "
                + f"saw {other.name} "
                + f"in the middle of {other.get_event().get_describe(False)}.\n"
                + f"{agent.name} "
                + "is initiating a conversation with "
                + f"{other.name}."
        )

        conversation = "\n".join(["{}: {}".format(n, u) for n, u in chats])
        conversation = (
                conversation or "[The conversation has not started yet -- start it!]"
        )

        prompt = f"Context for the task:\n\nPART 1. Abstract of {agent.name}\nHere is a brief description of {agent.name}:\n"
        prompt += self._base_desc()
        prompt += f"\nHere is the memory that is in {agent.name}'s head:"
        prompt += "\n- " + "\n- ".join([n.describe for n in nodes])
        prompt += "\n\nPART 2. Past Context\n" + pass_context
        prompt += f"\n\nCurrent Location: {address[-1]} in {address[-2]}"
        prompt += f"\n\nCurrent Context: {curr_context}"
        prompt += f"\n\n{agent.name} and {other.name} are chatting. Here is their conversation so far:\n{conversation}"
        prompt += f"\n---\nTask: Given the context above, what should {agent.name} say to {other.name} next in the conversation? And did it end the conversation?"
        prompt += "\n\nOutput a json of the following format:\n"
        prompt += f"""{{
    "{agent.name}": "<{agent.name}'s utterance>",
    "End the conversation": "<json Boolean>"
}}"""

        def _callback(response):
            assert "{" in response and "}" in response
            json_content = utils.load_dict(
                "{" + response.split("{")[1].split("}")[0] + "}"
            )
            end_chat = json_content["End the conversation"]
            if end_chat in ("false", "no", False):
                end_chat = False
            elif end_chat in ("true", "yes", True):
                end_chat = True
            return (json_content[agent.name], end_chat)

        return {
            "prompt": prompt,
            "callback": _callback,
            "failsafe": (
                "It's nice talking with you, looking forward to next time!",
                True,
            ),
        }

    def prompt_summarize_chats(self, chats):
        conversation = "\n".join(["{}: {}".format(n, u) for n, u in chats])
        prompt = f"""Conversation:
{conversation}

Summarize the conversation above in one short sentence without comma:
"""

        def _callback(response):
            return response.strip(".")

        return {
            "prompt": prompt,
            "callback": _callback,
            "failsafe": "general chatting between {} and {}".format(
                chats[0][0], chats[1][0]
            ),
        }

    def prompt_reflect_focus(self, nodes, topk):
        prompt = "[Information]\n" + "\n".join(
            ["{}. {}".format(idx, n.describe) for idx, n in enumerate(nodes)]
        )
        prompt += f"\n\nGiven the information above, what are {topk} most salient high-level questions?\n1. "

        def _callback(response):
            pattern = ["^\d{1}\. (.*)", "^\d{1} (.*)"]
            return parse_llm_output(response, pattern, mode="match_all")

        return {
            "prompt": prompt,
            "callback": _callback,
            "failsafe": [
                "Who is {}?".format(self.name),
                "Where do {} lives?".format(self.name),
                "What should {} do today?".format(self.name),
            ],
        }

    def prompt_reflect_insights(self, nodes, topk):
        prompt = (
                "[Statements]\n"
                + "\n".join(
            ["{}. {}".format(idx, n.describe) for idx, n in enumerate(nodes)]
        )
                + "\n\n"
        )
        prompt += f"What {topk} high-level insights can you infer from the above statements? (example format: insight (because of 1, 5, 3))\n1."

        def _callback(response):
            patterns = [
                "^\d{1}\. (.*)\. \(Because of (.*)\)",
                "^\d{1}\. (.*)\. \(because of (.*)\)",
                "^Insight \d{1}: (.*)\. \(Because of (.*)\)",
                "^Insight \d{1}: (.*)\. \(because of (.*)\)",
                "^Insight: (.*)\. \(Because of (.*)\)",
                "^Insight: (.*)\. \(because of (.*)\)",
                "^\d{1}\. (.*)\.",
                "^Insight \d{1}: (.*)\.",
            ]
            insights, outputs = [], parse_llm_output(
                response, patterns, mode="match_all"
            )
            if outputs:
                for output in outputs:
                    if isinstance(output, str):
                        insight, node_ids = output, []
                    elif len(output) == 2:
                        insight, reason = output
                        indices = [int(e.strip()) for e in reason.split(",")]
                        node_ids = [nodes[i].node_id for i in indices if i < len(nodes)]
                    insights.append([insight, node_ids])
                return insights
            raise Exception("Can not find insights")

        return {
            "prompt": prompt,
            "callback": _callback,
            "failsafe": [
                [
                    "{} is thinking on what to do next".format(self.name),
                    [nodes[0].node_id],
                ]
            ],
        }

    def prompt_reflect_chat_planing(self, chats):
        all_chats = "\n".join(["{}: {}".format(n, c) for n, c in chats])
        prompt = f"""[Conversation]
{all_chats}\n
Write down if there is anything from the conversation that {self.name} need to remember for her planning, from {self.name}'s perspective, in a full sentence.
"""

        def _callback(response):
            return response

        return {
            "prompt": prompt,
            "callback": _callback,
            "failsafe": f"{self.name} had a sonversation",
        }

    def prompt_reflect_chat_memory(self, chats):
        all_chats = "\n".join(["{}: {}".format(n, c) for n, c in chats])
        prompt = f"""[Conversation]
{all_chats}\n
Write down if there is anything from the conversation that {self.name} might have found interesting from {self.name}'s perspective, in a full sentence.
"""

        def _callback(response):
            return response

        return {
            "prompt": prompt,
            "callback": _callback,
            "failsafe": f"{self.name} had a sonversation",
        }

    def prompt_retrieve_plan(self, nodes):
        statements = [
            n.create.strftime("%A %B %d -- %H:%M %p") + ": " + n.describe for n in nodes
        ]
        prompt = "[Statements]" + "\n" + "\n".join(statements) + "\n\n"
        prompt += f"Given the statements above, is there anything that {self.name} should remember when planing for {utils.get_timer().get_date('%A %B %d')}?\n"
        prompt += f"If there is any scheduling information, be as specific as possible (include date, time, and location if stated in the statement)\n\n"
        prompt += f"Write the response from {self.name}'s perspective in lines, each line contains ONE thing to remember."

        def _callback(response):
            pattern = "^\d{1,2}\. (.*)\."
            return parse_llm_output(response, pattern, mode="match_all")

        return {
            "prompt": prompt,
            "callback": _callback,
            "failsafe": [r.describe for r in random.choices(nodes, k=10)],
        }

    def prompt_retrieve_thought(self, nodes):
        statements = [
            n.create.strftime("%A %B %d -- %H:%M %p") + ": " + n.describe for n in nodes
        ]
        prompt = "[Statements]" + "\n" + "\n".join(statements) + "\n\n"
        prompt += f"Given the statements above, how might we summarize {self.name}'s feelings up to now?\n\n"
        prompt += f"Write the response from {self.name}'s perspective in ONE sentence."

        def _callback(response):
            return response

        return {
            "prompt": prompt,
            "callback": _callback,
            "failsafe": "{} should follow the schedule of yesterday".format(self.name),
        }

    def prompt_retrieve_currently(self, plan_note, thought_note):
        time_stamp = (
                utils.get_timer().get_date() - datetime.timedelta(days=1)
        ).strftime("%A %B %d")
        prompt = f"{self.name}'s status from {time_stamp}:\n"
        prompt += f"{self.currently}\n\n"
        prompt += f"{self.name} remember these things at the end of {time_stamp}:\n"
        prompt += ". ".join(plan_note) + "\n\n"
        prompt += f"{self.name}'s feeling at the end of {time_stamp}:\n"
        prompt += thought_note + "\n\n"
        prompt += f"It is now {utils.get_timer().get_date('%A %B %d')}. Given the above, write {self.name}'s status for {utils.get_timer().get_date('%A %B %d')} that reflects {self.name}'s thoughts at the end of {time_stamp}.\n"
        prompt += (
            f"Write this in third-person talking about {self.name} in ONE sentence. "
        )
        prompt += "Follow this format below:\nStatus: <new status>"

        def _callback(response):
            pattern = "^Status: (.*)\."
            return parse_llm_output(response, pattern)

        return {
            "prompt": prompt,
            "callback": _callback,
            "failsafe": self.currently,
        }
