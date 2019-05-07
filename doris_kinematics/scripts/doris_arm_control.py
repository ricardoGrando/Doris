#! /usr/bin/env python
import time
import math
import numpy as np

import rospy
from std_msgs.msg import *
from inno_arm_control_msgs.msg import *

from kinematics import *



from gazebo_msgs.srv import GetLinkState 
from gazebo_msgs.srv import GetModelState
from gazebo_msgs.srv import SetLinkState 
from gazebo_msgs.srv import SetModelState
from gazebo_msgs.msg import LinkState # For getting information about link states
import time
from std_msgs.msg import Float64
from gazebo_msgs.srv import SpawnModel
import geometry_msgs.msg




topicList = [   '/doris/shoulder_yaw_joint_position_controller/command',
                '/doris/shoulder_pitch_joint_up_position_controller/command',                               
                '/doris/elbow_pitch_joint_up_position_controller/command',                
                '/doris/gripper_pitch_joint_position_controller/command',
                '/doris/gripper_yaw_joint_position_controller/command',
                '/doris/gripper_roll_joint_position_controller/command'
                #'/doris/gripper_right_joint_position_controller/command',
                #'/doris/gripper_left_joint_position_controller/command'
            ]

publishers = []

for topic in topicList:
    publishers.append(rospy.Publisher(topic, Float64, queue_size=10))

shoulder_elbow_joint = rospy.Publisher('/doris/shoulder_elbow_joint_position_controller/command', Float64, queue_size=10)
shoulder_pitch_joint_down = rospy.Publisher('/doris/shoulder_pitch_joint_down_position_controller/command', Float64, queue_size=10)
elbow_pitch_joint_down = rospy.Publisher('/doris/elbow_pitch_joint_down_position_controller/command', Float64, queue_size=10)
hearth_pitch_joint_down = rospy.Publisher('/doris/hearth_joint_position_controller/command', Float64, queue_size=10)



def inverse_kinematics_callback(data):
    # Pegar o target_end_effector da mensagem recebida e converter para array de numpy
    target_position = np.array([data.target_end_effector[0], data.target_end_effector[1], data.target_end_effector[2], data.target_end_effector[3], data.target_end_effector[4], data.target_end_effector[5]])

    # Angulos da posicao inicial
    angles = np.array([0.1,0.1,0.1,0.1,0.1,0.1]) 

    # Taxa de sleep
    rate = rospy.Rate(10)

    print("asdfasd")
    
    while(True):
		# Realizar a cinematica direta para obter a posicao e orientacao cartesiana do end effector
        atual_position = forwardKinematics(angles)
        distance = target_position - atual_position
            
        if (max(abs(target_position - atual_position)) > 2.0):
            J = calc_jacobian(angles)
            # Inverter a matriz
            J_inv = np.linalg.inv(J)
            # Calcular o delta do end_effector
            # O MAIOR ELEMENTO DO VETOR DO DELTA DO END EFFECTOR NAO PODE SER MAIOR QUE step_size
            delta_end_effector = ((distance)*data.step_size)/np.max(max(distance))
            print(delta_end_effector)
            # Calcular o delta dos angulos, dado esse delta do end effector
            delta_angles = J_inv.dot(delta_end_effector)
            # Calcular os novos angulos
            angles += delta_angles			
            # Normalizar cada angulo em seus respectivos limites para enviar para os motores. Exemplo: angles[0] entre theta_0_max e theta_0_min
            # Normalizacao = (valor - valor_min)/(valor_max - valor_min)
            print(atual_position)
            # raw_angles = norm_angles(angles)
            # Publicar os angulos com o publisher
            for i in range(0, len(publishers)):
                publishers[i].publish(angles[i])            
            
            # Dormir pelo tempo definido
            time.sleep(0.5)            
            rate.sleep()
        else:
            print("Arrived!!!")
            rate.sleep()

def inno_arm_control():
	
	# Criar o nodo da aplicacao com o nome: inno_arm_control		
	rospy.init_node("doris_arm_control", anonymous=False)

	# Criar o subscriber para o topico "/set_joint_angles"
	# Esse topico recebe um objeto do tipo CartesianMsg
	# CartesianMsg:
	#   float64[] target_end_effector
	#   float64 step_size
	# Sendo target_end_effector a posicao no espaco desejada step_size o tamanho do passo para chegar la
	# O callback do subscriber tem que ser a funcao: inverse_kinematics_callback
	rospy.Subscriber('/doris_arm_target_position', CartesianMsg, inverse_kinematics_callback)
	
	rospy.spin()

####################################### Exemplo para testar a aplicacao #######################################
# rostopic pub -1 /cartesian_position inno_arm_control_msgs/CartesianMsg "target_end_effector: [-17, 2, 20, -2.7, 1.46, 2.67] step_size: 0.1"		

# if __name__ == "__main__":       
#     try:
#         inno_arm_control()
#     except rospy.ROSInterruptException:
#         pass

def spawnObject(count, posx, posy, posz):
        
    spawn = rospy.ServiceProxy("gazebo/spawn_sdf_model", SpawnModel)

    rospy.wait_for_service("gazebo/spawn_sdf_model")

    initial_pose = geometry_msgs.msg.Pose()
    initial_pose.position.x = posx
    initial_pose.position.y = posy
    initial_pose.position.z = posz

    f = open('/home/nautec/.gazebo/models/cube_spiral/model.sdf','r')
    sdff = f.read()

    print spawn("cube"+str(count), sdff, "default", initial_pose, "world")
 
        

# self.endEffectorService.spawnObject(spawnCount, self.endEffectorService.pos_x, \
#                                                 self.endEffectorService.pos_y, self.endEffectorService.pos_z)

def spiral(stepSize, radius, endEffectorPosition, numberSpirals):
  endEffector = np.zeros(shape=(int(2*math.pi*radius/stepSize)*numberSpirals,6))
  endEffector[:] = endEffectorPosition
        
  angle = math.asin(stepSize/(radius))
    
  for i in range(0, endEffector.shape[0]):
    endEffector[i][2] = endEffector[i][2] - radius*stepSize*(i+1)       
    endEffector[i][0] = endEffector[i][0] + radius*math.cos(angle*(i+1)) - radius
    endEffector[i][1] = endEffector[i][1] + radius*math.sin(angle*(i+1))
        
    if i > 0:
      dx = (endEffector[i][0] - endEffector[i-1][0])
      dy = (endEffector[i][1] - endEffector[i-1][1])
      dz = (endEffector[i][2] - endEffector[i-1][2])
      d =  ( dx**2 + dy**2 + dz**2 )**(0.5)
            
  return endEffector

if __name__ == "__main__":  

    rospy.init_node("doris_arm_control", anonymous=False)

    endEffectorPosition = np.array([0.5447546532517447, 0.0, 0.8987512626584708, 1.5707963267948966, 0.0, 1.57079632679489666])

    trajectory = spiral(0.01, 0.075, endEffectorPosition, 4)

    angles = np.array([0,math.pi/4,-math.pi/4,0.0,0.0,0.1]) 

    rate = rospy.Rate(10)

    for j in range(0, len(publishers)):
        publishers[j].publish(angles[j])  
        if 'shoulder_pitch' in topicList[j]:
            shoulder_pitch_joint_down.publish(angles[j])
            shoulder_elbow_joint.publish(-angles[j])
        if 'elbow_pitch_joint' in topicList[j]:
            elbow_pitch_joint_down.publish(angles[j])
            hearth_pitch_joint_down.publish(-angles[j]) 
        rate.sleep()

    raw_input()

    for i in range(1, trajectory.shape[0]):
		# Realizar a cinematica direta para obter a posicao e orientacao cartesiana do end effector
        atual_position = forwardKinematics(angles)
        
        J = calc_jacobian(angles)
        # Inverter a matriz
        J_inv = np.linalg.pinv(J)
        # Calcular o delta do end_effector
        # O MAIOR ELEMENTO DO VETOR DO DELTA DO END EFFECTOR NAO PODE SER MAIOR QUE step_size
        delta_end_effector = trajectory[i] - trajectory[i-1]
        # Calcular o delta dos angulos, dado esse delta do end effector
        delta_angles = J_inv.dot(delta_end_effector)
        # Calcular os novos angulos
        angles += delta_angles			
        # Normalizar cada angulo em seus respectivos limites para enviar para os motores. Exemplo: angles[0] entre theta_0_max e theta_0_min
        # Normalizacao = (valor - valor_min)/(valor_max - valor_min)
        print(atual_position)
        # raw_angles = norm_angles(angles)
        # Publicar os angulos com o publisher
        for j in range(0, len(publishers)):
            publishers[j].publish(angles[j])  
            if 'shoulder_pitch' in topicList[j]:
                shoulder_pitch_joint_down.publish(angles[j])
                shoulder_elbow_joint.publish(-angles[j])
            if 'elbow_pitch_joint' in topicList[j]:
                elbow_pitch_joint_down.publish(angles[j])
                hearth_pitch_joint_down.publish(-angles[j])            

        #atual_position[0] = 

        spawnObject(i, atual_position[0], atual_position[1], atual_position[2])
        
        # Dormir pelo tempo definido
        #time.sleep(0.1)            
        rate.sleep()
        