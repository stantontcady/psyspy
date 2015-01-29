from math import cos, sin


def fp_fq_helper(P_injected, Q_injected, Vpolar_i, Yii, admittance_matrix_index_bus_id_mapping,
                 voltage_list, connected_bus_ids, interconnection_admittance_list):
    
    (P_network, Q_network) = compute_apparent_power_injected_from_network(Vpolar_i, Yii,
                                                                          admittance_matrix_index_bus_id_mapping,
                                                                          voltage_list, connected_bus_ids,
                                                                          interconnection_admittance_list)

    return P_network - P_injected, Q_network - Q_injected
    
               
def connected_bus_helper(Vpolar_i, Vpolar_j, Yij, real_trig_function, imag_trig_function, imag_multipler=1):
    _, thetai = Vpolar_i
    Vj, thetaj = Vpolar_j
    return Vj*trig_helper(thetai, thetaj, Yij, real_trig_function, imag_trig_function, imag_multipler)


def trig_helper(thetai, thetaj, Yij, real_trig_function, imag_trig_function, imag_multipler=1):
    Gij, Bij = Yij
    return Gij*real_trig_function(thetai - thetaj) + imag_multipler*Bij*imag_trig_function(thetai - thetaj)


def jacobian_hij_helper(Vpolar_i, Vpolar_j, Yij, Lij=None):
    if Lij is not None:
        Vj, _ = Vpolar_j
        return Lij*Vj
    else:
        Vi, thetai = Vpolar_i
        Vj, thetaj = Vpolar_j
        return Vi*Vj*trig_helper(thetai, thetaj, Yij, sin, cos)


def jacobian_nij_helper(Vpolar_i, Vpolar_j, Yij, Kij=None):
    if Kij is not None:
        Vj, _ = Vpolar_j
        return -1*Kij/Vj
    else:
        Vi, thetai = Vpolar_i
        _, thetaj = Vpolar_j
        return Vi*trig_helper(thetai, thetaj, Yij, cos, sin, -1)


def jacobian_kij_helper(Vpolar_i, Vpolar_j, Yij, Nij=None):
    if Nij is not None:
        Vj, _ = Vpolar_j
        return -1*Nij*Vj
    else:
        Vi, thetai = Vpolar_i
        Vj, thetaj = Vpolar_j
        return -1*Vi*Vj*trig_helper(thetai, thetaj, Yij, cos, sin, -1)


def jacobian_lij_helper(Vpolar_i, Vpolar_j, Yij, Hij=None):
    if Hij is not None:
        Vj, _ = Vpolar_j
        return Hij/Vj
    else:
        Vi, thetai = Vpolar_i
        _, thetaj = Vpolar_j
        return Vi*trig_helper(thetai, thetaj, Yij, sin, cos)


def jacobian_diagonal_helper(Vpolar_i, Yii, voltage_is_static,
                             admittance_matrix_index_bus_id_mapping,
                             voltage_list, connected_bus_ids,
                             interconnection_admittance_list):
    
    Vi, _ = Vpolar_i
    Hii = 0
    # if pv bus, voltage magnitude will be static, voltage magnitude static is first element of tuple 
    if is_pv_bus(voltage_is_static) is False:
        Gii, Bii = Yii
        Nii = 2*Gii*Vi
        Kii = 0
        Lii = 2*Bii*Vi
    else:
        Nii = None
        Kii = None
        Lii = None

    for index_k, bus_id_k in enumerate(connected_bus_ids):           
        admittance_matrix_index_k = admittance_matrix_index_bus_id_mapping.index(bus_id_k)
        Vpolar_k = voltage_list[admittance_matrix_index_k]
        Yik = interconnection_admittance_list[index_k]
        
        H_L_ii = connected_bus_helper(Vpolar_i, Vpolar_k, Yik, sin, cos)
        
        Hii += H_L_ii
        if is_pv_bus(voltage_is_static) is False:
            N_K_ii = connected_bus_helper(Vpolar_i, Vpolar_k, Yik, cos, sin, -1)
            Nii += N_K_ii
            Kii += N_K_ii
            Lii += H_L_ii

    Hii = -1*Vi*Hii
    if is_pv_bus(voltage_is_static) is False:
        Kii *= Vi
    
    return Hii, Nii, Kii, Lii


def compute_apparent_power_injected_from_network(Vpolar_i, Yii, admittance_matrix_index_bus_id_mapping,
                                                 voltage_list, connected_bus_ids, interconnection_admittance_list):

    Vi, _ = Vpolar_i
    Gii, Bii = Yii
    P = Gii*Vi
    Q = Bii*Vi
    for index_k, bus_id_k in enumerate(connected_bus_ids):
        admittance_matrix_index_k = admittance_matrix_index_bus_id_mapping.index(bus_id_k)
        Vpolar_k = voltage_list[admittance_matrix_index_k]
        Yik = interconnection_admittance_list[index_k]

        P += connected_bus_helper(Vpolar_i, Vpolar_k, Yik, cos, sin, -1)
        Q += connected_bus_helper(Vpolar_i, Vpolar_k, Yik, sin, cos)

    P *= Vi
    Q *= Vi
    return P, Q


def is_slack_bus(voltage_is_static):
    if voltage_is_static[0] is True and voltage_is_static[1] is True:
        return True

    return False

    
def is_pv_bus(voltage_is_static):
    return voltage_is_static[0]


def compute_jacobian_row_by_bus(J, index_i,
                                voltage_is_static_list, has_dynamic_model_list, connected_bus_ids_list,
                                jacobian_indices, admittance_matrix_index_bus_id_mapping,
                                interconnection_admittance_list, self_admittance_list,
                                voltage_list, dgr_derivatives):

    # if voltage magnitude and angle are constant, this bus is not included in the jacboian
    if is_slack_bus(voltage_is_static_list[index_i]) is True:
        return
    
    Vpolar_i = voltage_list[index_i]
    Yii = self_admittance_list[index_i]

    
    connected_bus_ids = connected_bus_ids_list[index_i]
    interconnection_admittance = interconnection_admittance_list[index_i]
    
    Hii, Nii, Kii, Lii = jacobian_diagonal_helper(Vpolar_i, Yii, voltage_is_static_list[index_i],
                                                  admittance_matrix_index_bus_id_mapping,
                                                  voltage_list, connected_bus_ids,
                                                  interconnection_admittance)
    
    i = jacobian_indices[index_i]
    
    J[i, i] = Hii    
    if is_pv_bus(voltage_is_static_list[index_i]) is False:
        J[i+1, i] = Kii
        J[i, i+1] = Nii
        J[i+1, i+1] = Lii
        if has_dynamic_model_list[index_i] is True:
            Hii_dgr, Nii_dgr, Kii_dgr, Lii_dgr = dgr_derivatives[index_i]
            J[i, i] -= Hii_dgr
            J[i, i+1] -= Nii_dgr
            J[i+1, i] -= Kii_dgr
            J[i+1, i+1] -= Lii_dgr
    
    for connected_bus_index_j, bus_id_j in enumerate(connected_bus_ids):
        index_j = admittance_matrix_index_bus_id_mapping.index(bus_id_j)
        if is_slack_bus(voltage_is_static_list[index_j]) is False:
            j = jacobian_indices[index_j]

            Vpolar_j = voltage_list[index_j]
            Yij = interconnection_admittance[connected_bus_index_j]
            
            J[i, j] = jacobian_hij_helper(Vpolar_i, Vpolar_j, Yij, Lij=None)

            if is_pv_bus(voltage_is_static_list[index_i]) is False:
                J[i+1, j] = jacobian_kij_helper(Vpolar_i, Vpolar_j, Yij, Nij=None)
                Kij = J[i+1, j]
            else:
                Kij = None

            if is_pv_bus(voltage_is_static_list[index_j]) is False:
                if is_pv_bus(voltage_is_static_list[index_i]) is False:
                    J[i+1, j+1] = jacobian_lij_helper(Vpolar_i, Vpolar_j, Yij, Hij=J[i, j])

                J[i, j+1] = jacobian_nij_helper(Vpolar_i, Vpolar_j, Yij, Kij=Kij)
