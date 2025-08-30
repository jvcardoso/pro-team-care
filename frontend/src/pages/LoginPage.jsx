import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import { authService } from '../services/api'

const LoginPage = () => {
  const navigate = useNavigate()
  const [formData, setFormData] = useState({
    email: '',
    password: ''
  })
  const [isLoading, setIsLoading] = useState(false)

  useEffect(() => {
    // Verificar se já está logado
    const token = localStorage.getItem('access_token')
    if (token) {
      // Verificar se há uma URL para redirecionar
      const redirectUrl = sessionStorage.getItem('redirectAfterLogin')
      if (redirectUrl) {
        sessionStorage.removeItem('redirectAfterLogin')
        navigate(redirectUrl, { replace: true })
      } else {
        navigate('/admin', { replace: true })
      }
    }
  }, [navigate])

  const handleSubmit = async (e) => {
    e.preventDefault()
    setIsLoading(true)

    try {
      const response = await authService.login(formData.email, formData.password)

      // Salvar token
      localStorage.setItem('access_token', response.access_token)

      toast.success('Login realizado com sucesso!')

      // Verificar se há uma URL para redirecionar
      const redirectUrl = sessionStorage.getItem('redirectAfterLogin')
      if (redirectUrl) {
        sessionStorage.removeItem('redirectAfterLogin')
        navigate(redirectUrl, { replace: true })
      } else {
        navigate('/admin', { replace: true })
      }
    } catch (error) {
      console.error('Erro no login:', error)
      toast.error(error.response?.data?.detail || 'Erro no login. Verifique suas credenciais.')
    } finally {
      setIsLoading(false)
    }
  }

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    })
  }

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <h2 className="mt-6 text-center text-3xl font-bold text-gray-900">
          Pro Team Care
        </h2>
        <p className="mt-2 text-center text-sm text-gray-600">
          Faça login em sua conta
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white py-8 px-4 shadow sm:rounded-lg sm:px-10">
          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700">
                Email
              </label>
              <div className="mt-1">
                <input
                  id="email"
                  name="email"
                  type="email"
                  autoComplete="email"
                  required
                  value={formData.email}
                  onChange={handleChange}
                  className="input-field"
                  placeholder="seu@email.com"
                />
              </div>
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-700">
                Senha
              </label>
              <div className="mt-1">
                <input
                  id="password"
                  name="password"
                  type="password"
                  autoComplete="current-password"
                  required
                  value={formData.password}
                  onChange={handleChange}
                  className="input-field"
                  placeholder="••••••••"
                />
              </div>
            </div>

            <div>
              <button
                type="submit"
                disabled={isLoading}
                className="w-full btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isLoading ? (
                  <>
                    <span className="loading-spinner mr-2"></span>
                    Entrando...
                  </>
                ) : (
                  'Entrar'
                )}
              </button>
            </div>
          </form>

          <div className="mt-6">
            <div className="text-center">
              <span className="text-sm text-gray-600">
                Sistema de Gestão Profissional v1.0.0
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default LoginPage