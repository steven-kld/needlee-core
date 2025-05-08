# user_id = "825098b6-524d-48da-8c03-ac2c00c705a3"
# user_contact = "long"
# interview_id = 1
# organization_id = 1
# attempt = None

# from services.process_manager import ProcessManager

# process = ProcessManager(organization_id, interview_id, user_id, attempt)
# process.process()

# import os

# email = "demo@needlee.ai"
# password = "test"

# from dotenv import load_dotenv
# from entities.organizations import (
#     check_creds,
#     set_password
# )


# load_dotenv()


# if __name__ == "__main__":
#     print(check_creds(email, password))
    # print(get_interview_by_id(1,1))
    # set_password(password, email)

from services.interview_generator import InterviewGenerator

text = """
The attack on Pearl Harbor[nb 3] was a surprise military strike by the Empire of Japan on the United States Pacific Fleet at its naval base at Pearl Harbor on Oahu, Hawaii, on December 7, 1941. At the time, the U.S. was a neutral country in World War II. The air raid on Pearl Harbor, which was launched from aircraft carriers, resulted in the U.S. entering the war on the side of the Allies on the day following the attack. The Japanese military leadership referred to the attack as the Hawaii Operation and Operation AI,[nb 4] and as Operation Z during its planning.[14][15][16]

The attack on Pearl Harbor was preceded by months of negotiations between the U.S. and Japan over the future of the Pacific. Japanese demands included that the U.S. end its sanctions against Japan, cease aiding China in the Second Sino-Japanese War, and allow Japan to access the resources of the Dutch East Indies. Japan sent out its naval attack group on November 26, 1941, just prior to receiving the Hull note, which stated the U.S. desire that Japan withdraw from China and French Indochina. Isoroku Yamamoto, commander of the Japanese Combined Fleet, planned the attack as a pre-emptive strike on the Pacific Fleet, based at Pearl Harbor since 1940 in order to prevent it from interfering with Japan's planned actions in Southeast Asia. Yamamoto hoped that the strike would enable Japan to make quick territorial gains and negotiate a peace. In addition to Pearl Harbor, over seven hours Japan launched coordinated attacks on the U.S.-held Philippines, Guam, and Wake Island; and on the British Empire in Malaya, Singapore, and Hong Kong.[17]

The attack force, commanded by Chūichi Nagumo, began its attacks at 7:48 a.m. Hawaiian time (6:18 p.m. GMT) on December 7, 1941.[nb 5] The base was attacked by 353 fighters, level and dive bombers, and torpedo bombers in two waves launched from six aircraft carriers.[18] Of the eight U.S. battleships present, all were damaged and four were sunk. All but Arizona were later raised, and six were returned to service during the war. The Japanese also sank or damaged three cruisers, three destroyers, an anti-aircraft training ship,[nb 6] and a minelayer. More than 180 U.S. aircraft were destroyed.[20] A total of 2,403 Americans were killed and 1,178 others were wounded, while the Japanese lost a total of 29 aircraft, five midget submarines, and 130 men. The three U.S. carriers stationed at Pearl Harbor were at sea at the time, and important base installations, including its oil storage and naval repair facilities, were not attacked. 
"""

gen = InterviewGenerator(1)
gen.from_raw_text(text)
print(gen.to_dict())
# print