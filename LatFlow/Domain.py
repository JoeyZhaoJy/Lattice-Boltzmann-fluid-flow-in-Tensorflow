
import numpy as np
import tensorflow as tf
import matplotlib.pyplot as plt


import D2Q9

class Domain():
  def __init__(self,
               method,
               nu, 
               Ndim,
               boundary,
               dx=1.0,
               dt=1.0):
    if method == "D2Q9":
      self.Nneigh = 9
      self.Dim    = 2
      self.W      = D2Q9.WEIGHTS
      self.C      = D2Q9.LVELOC
      self.Op     = D2Q9.OPPOSITE
      self.St     = D2Q9.STREAM

    if nu is not list:
      nu = [nu]
   
    self.time   = 0.0
    self.dt     = dt
    self.dx     = dx
    self.Cs     = dx/dt
    self.Step   = 1
    self.Sc     = 0.17
    self.Ndim   = Ndim
    self.Ncells = np.prod(np.array(Ndim))
    self.boundary = tf.constant(boundary)

    self.Nl     = len(nu)
    self.tau    = []
    self.G      = []
    self.Gs     = []
    self.Rhoref = []
    self.Psi    = []
    self.Gmix   = 0.0
      
    self.F       = []
    self.Ftemp   = []
    self.Vel     = []
    self.BForce  = []
    self.Rho     = []
    self.IsSolid = []
  
    for i in xrange(len(nu)):
      self.tau.append(     3.0*nu[i]*self.dt/(self.dx*self.dx)+0.5)
      self.G.append(       0.0)
      self.Gs.append(      0.0)
      self.Rhoref.append(  200.0)
      self.Psi.append(     4.0)
      self.F.append(       tf.Variable([1] + Ndim + [self.Nneigh]))
      self.Ftemp.append(   tf.Variable([1] + Ndim + [self.Nneigh]))
      self.Vel.append(     tf.Variable([1] + Ndim + [3]))
      self.BForce.append(  tf.Variable([1] + Ndim + [3]))
      self.Rho.append(     tf.Variable([1] + Ndim + [1]))
      self.IsSolid.append( tf.Variable([1] + Ndim + [1]))

    self.EEk = tf.zeros((self.Nneigh))
    for n in xrange(3):
      for m in xrange(3):
        self.EEk = self.EEk + tf.abs(self.C[:,n] * self.C[:,m])

    def CollideSC():
      f_boundary = tf.multiply(self.F[0], self.boundary)
      f_no_boundary = tf.multiply(self.F[0], (1.0-self.boundary))
      vel_no_boundary = tf.multiply(self.Vel[0], (1.0-self.boundary))
      bforce_no_boundary = tf.multiply(self.BForce[0], (1.0-self.boundary))
      rho_no_boundary = tf.multiply(self.Rho[0], (1.0-self.boundary))
      vel = vel_no_boundary + self.dt*self.tau[0]*(bforce_no_boundary/rho_no_boundary)
      vel_dot_vel = tf.expand_dims(tf.reduce_sum(vel * vel, axis=3))
      vel_dot_c = tf.reduce_sum(tf.expand_dims(vel, axis=3) * tf.reshape(self.C, [1,1,1,self.Nneigh,3]), axis=4)
      Feq = tf.reshape(self.W, [1,1,1,self.Nneigh]) * rho_no_boundary * (1.0 + 3.0*vel_dot_c/self.Cs + 4.5*vel_dot_c*vel_dot_c/(self.Cs*self.Cs) - 1.5*vel_dot_vel/(self.Cs*self.Cs))
      NonEq = f_no_boundary - Feq
      Q = tf.expand_dims(tf.reduce_sum(NonEq*NonEq*tf.reshape(self.EEk, [1,1,1, self.Nneigh]), axis=3), axis=3)
      Q = tf.sqrt(2.0*Q)
      tau = 0.5*(tau+tf.sqrt(tau*tau + 6.0*Q*self.Sc/rho_no_boundary))
      f_no_boundary = f_no_boundary - NonEq/tau
      collid_step = self.F[0].assign(f_no_boundary)
      return collid_step

    def StreamSC():
      # stream f
      f_pad = pad_mobius(self.F[0])
      f_pad = simple_conv(f_pad, self.St)
      # calc new velocity and density
      Rho = tf.expand_dims(tf.reduce_sum(f_pad, 3), 3)
      Rho = tf.multiply(Rho, (1.0 - self.boundary))
      Vel = simple_conv(f_pad, self.C)
      Vel = tf.multiply(Vel, (1.0 - self.boundary))
      Vel = tf.multiply(Vel, Rho)
      # create steps
      stream_step = self.F[0].assign(f_pad)
      Rho_step = self.Rho[0].assign(Rho)
      Vel_step = self.Vel[0].assign(Vel)
      step = tf.group([stream_step, Rho_step, Vel_step])
      return step
 
    def Initialize():
      f_zero = tf.constant(np.zeros([1] + self.Ndim + [self.Nneigh]), dtype=np.float32)
      f_zero = f_zero + tf.reshape(self.W, [1,1,1] + [self.Nneigh])
      assign_step = self.F.assign(f_zero)
      return assign_step 
 
    def Solve(sess, num_steps=10):
      # make steps
      assign_step = self.Initialize()
      stream_step = self.StreamSC() 
      collide_step = self.CollideSC()

      # run solver
      sess.run(assign_step)
      for i in xrange(num_steps):
        np_f = sess.run(self.Vel)
        np_f = np.sum(np_f, axis=np.len(np_f))
        plt.imshow(np_f)
        plt.show()
    
        sess.run(stream_step)
        sess.run(collide_step)
      
           
      
       





      
  
