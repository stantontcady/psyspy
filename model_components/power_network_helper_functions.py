from math import cos, sin


def fp_fq_helper(P_net, Q_net, Vi, thetai, Gii, Bii,
                  admittance_matrix_index_bus_id_mapping,
                  voltage_mag_list, voltage_angle_list,
                  connected_bus_ids,
                  interconnection_conductances_list,
                  interconnection_susceptances_list):
    
    (P_network, Q_network) = compute_apparent_power_injected_from_network(Vi, thetai, Gii, Bii,
                                                                          admittance_matrix_index_bus_id_mapping,
                                                                          voltage_mag_list, voltage_angle_list,
                                                                          connected_bus_ids,
                                                                          interconnection_conductances_list,
                                                                          interconnection_susceptances_list)

    return P_network - P_net, Q_network - Q_net
    
               
def connected_bus_helper(thetai, Vk, thetak, Gik, Bik, real_trig_function, imag_trig_function, imag_multipler=1):
    return Vk*(Gik*real_trig_function(thetai - thetak) + imag_multipler*Bik*imag_trig_function(thetai - thetak))


def jacobian_hij_helper(Vi, thetai, Vj, thetaj, Gij, Bij, Lij=None):
    if Lij is not None:
        return Lij*Vj
    else:
        return Vi*Vj*(Gij*sin(thetai - thetaj) + Bij*cos(thetai - thetaj))


def jacobian_nij_helper(Vi, thetai, Vj, thetaj, Gij, Bij, Kij=None):
    if Kij is not None:
        return -1*Kij/Vj
    else:
        return Vi*(Gij*cos(thetai - thetaj) - Bij*sin(thetai - thetaj))


def jacobian_kij_helper(Vi, thetai, Vj, thetaj, Gij, Bij, Nij=None):
    if Nij is not None:
        return -1*Nij*Vj
    else:
        return -1*Vi*Vj*(Gij*cos(thetai - thetaj) - Bij*sin(thetai - thetaj))


def jacobian_lij_helper(Vi, thetai, Vj, thetaj, Gij, Bij, Hij=None):
    if Hij is not None:
        return Hij/Vj
    else:
        return Vi*(Gij*sin(thetai - thetaj) + Bij*cos(thetai - thetaj))


def jacobian_diagonal_helper(Vi, thetai, Gii, Bii, is_pv_bus,
                              admittance_matrix_index_bus_id_mapping,
                              voltage_mag_list, voltage_angle_list,
                              connected_bus_ids,
                              interconnection_conductances_list,
                              interconnection_susceptances_list):
    
    Hii = 0                    
    if is_pv_bus is False:
        Nii = 2*Gii*Vi
        Kii = 0
        Lii = 2*Bii*Vi
    else:
        Nii = None
        Kii = None
        Lii = None

    for index_k, bus_id_k in enumerate(connected_bus_ids):           
        admittance_matrix_index_k = admittance_matrix_index_bus_id_mapping.index(bus_id_k)
        Vk = voltage_mag_list[admittance_matrix_index_k]
        thetak = voltage_angle_list[admittance_matrix_index_k]
        Gik = interconnection_conductances_list[index_k]
        Bik = interconnection_susceptances_list[index_k]
        
        H_L_ii = connected_bus_helper(thetai, Vk, thetak, Gik, Bik, sin, cos)
        
        Hii += H_L_ii
        if is_pv_bus is False:
            N_K_ii = connected_bus_helper(thetai, Vk, thetak, Gik, Bik, cos, sin, -1)
            Nii += N_K_ii
            Kii += N_K_ii
            Lii += H_L_ii

    Hii = -1*Vi*Hii
    if is_pv_bus is False:
        Kii *= Vi
    
    return Hii, Nii, Kii, Lii


def compute_apparent_power_injected_from_network(Vi, thetai, Gii, Bii,
                                                 admittance_matrix_index_bus_id_mapping,
                                                 voltage_mag_list, voltage_angle_list,
                                                 connected_bus_ids,
                                                 interconnection_conductances_list,
                                                 interconnection_susceptances_list):

    P = Gii*Vi
    Q = Bii*Vi
    for index_k, bus_id_k in enumerate(connected_bus_ids):
        admittance_matrix_index_k = admittance_matrix_index_bus_id_mapping.index(bus_id_k)
        Vk = voltage_mag_list[admittance_matrix_index_k]
        thetak = voltage_angle_list[admittance_matrix_index_k]
        Gik = interconnection_conductances_list[index_k]
        Bik = interconnection_susceptances_list[index_k]

        P += connected_bus_helper(thetai, Vk, thetak, Gik, Bik, cos, sin, -1)
        Q += connected_bus_helper(thetai, Vk, thetak, Gik, Bik, sin, cos)

    P *= Vi
    Q *= Vi
    return P, Q


def compute_jacobian_row_by_bus(J, index_i,
                                is_slack_bus_list, is_pv_bus_list, has_dynamic_dgr_list, connected_bus_ids_list,
                                jacobian_indices,
                                admittance_matrix_index_bus_id_mapping,
                                interconnection_conductances_list, interconnection_susceptances_list,
                                self_conductance_list, self_susceptance_list,
                                voltage_mag_list, voltage_angle_list, dgr_derivatives):

    if is_slack_bus_list[index_i] is True:
        return
    
    Vi = voltage_mag_list[index_i]
    thetai = voltage_angle_list[index_i]
    Gii = self_conductance_list[index_i]
    Bii = self_susceptance_list[index_i]
    
    connected_bus_ids = connected_bus_ids_list[index_i]
    interconnection_conductances = interconnection_conductances_list[index_i]
    interconnection_susceptances = interconnection_susceptances_list[index_i]
    
    Hii, Nii, Kii, Lii = jacobian_diagonal_helper(Vi, thetai, Gii, Bii, is_pv_bus_list[index_i],
                                                  admittance_matrix_index_bus_id_mapping,
                                                  voltage_mag_list, voltage_angle_list,
                                                  connected_bus_ids,
                                                  interconnection_conductances,
                                                  interconnection_susceptances)
    
    i = jacobian_indices[index_i]
    
    J[i, i] = Hii    
    if is_pv_bus_list[index_i] is False:
        J[i+1, i] = Kii
        J[i, i+1] = Nii
        J[i+1, i+1] = Lii
        if has_dynamic_dgr_list[index_i] is True:
            Hii_dgr, Nii_dgr, Kii_dgr, Lii_dgr = dgr_derivatives[index_i]
            J[i, i] -= Hii_dgr
            J[i, i+1] -= Nii_dgr
            J[i+1, i] -= Kii_dgr
            J[i+1, i+1] -= Lii_dgr
    
    for connected_bus_index_j, bus_id_j in enumerate(connected_bus_ids):
        index_j = admittance_matrix_index_bus_id_mapping.index(bus_id_j)
        if is_slack_bus_list[index_j] is False:
            j = jacobian_indices[index_j]

            Vj = voltage_mag_list[index_j]
            thetaj = voltage_angle_list[index_j]
            Gij = interconnection_conductances[connected_bus_index_j]
            Bij = interconnection_susceptances[connected_bus_index_j]
            
            J[i, j] = jacobian_hij_helper(Vi, thetai, Vj, thetaj, Gij, Bij, Lij=None)

            if is_pv_bus_list[index_i] is False:
                J[i+1, j] = jacobian_kij_helper(Vi, thetai, Vj, thetaj, Gij, Bij, Nij=None)
                Kij = J[i+1, j]
            else:
                Kij = None

            if is_pv_bus_list[index_j] is False:
                if is_pv_bus_list[index_i] is False:
                    J[i+1, j+1] = jacobian_lij_helper(Vi, thetai, Vj, thetaj, Gij, Bij, Hij=J[i, j])

                J[i, j+1] = jacobian_nij_helper(Vi, thetai, Vj, thetaj, Gij, Bij, Kij=Kij)
