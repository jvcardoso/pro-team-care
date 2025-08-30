import React, { useState } from 'react';
import Card from '../components/ui/Card';
import Button from '../components/ui/Button';
import Input from '../components/ui/Input';
import Textarea from '../components/ui/Textarea';

const LayoutDemo = () => {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    phone: '',
    message: ''
  });

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    console.log('Form submitted:', formData);
  };

  const statsData = [
    { title: 'Total Usuários', value: '1,245', color: 'primary', icon: '👥' },
    { title: 'Pacientes Ativos', value: '892', color: 'success', icon: '🏥' },
    { title: 'Consultas Hoje', value: '47', color: 'info', icon: '📅' },
    { title: 'Pendências', value: '12', color: 'warning', icon: '⏳' }
  ];

  return (
    <div className="space-y-6">
      <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-sm">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">Demonstração do Layout</h1>
        <p className="text-gray-600 dark:text-gray-400">Esta página demonstra os componentes do template AdminLTE implementado</p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
        {statsData.map((stat, index) => (
          <Card key={index} className={`card-${stat.color}`} shadow>
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm font-medium text-gray-600 dark:text-gray-400">{stat.title}</div>
                <div className="text-2xl font-bold text-gray-900 dark:text-white">{stat.value}</div>
              </div>
              <div className="text-3xl">{stat.icon}</div>
            </div>
          </Card>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        {/* Form Demo */}
        <div>
          <Card
            title="Formulário de Demonstração"
            subtitle="Exemplo de formulário usando os componentes criados"
            shadow
          >
            <form onSubmit={handleSubmit} className="space-y-4">
              <Input
                label="Nome Completo"
                name="name"
                value={formData.name}
                onChange={handleInputChange}
                placeholder="Digite seu nome completo"
                required
                leftIcon={
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M12 2C13.1 2 14 2.9 14 4C14 5.1 13.1 6 12 6C10.9 6 10 5.1 10 4C10 2.9 10.9 2 12 2ZM21 9V7L12 2L3 7V9C3 14.55 6.84 19.74 12 21C17.16 19.74 21 14.55 21 9Z"/>
                  </svg>
                }
              />

              <Input
                label="E-mail"
                name="email"
                type="email"
                value={formData.email}
                onChange={handleInputChange}
                placeholder="seu.email@exemplo.com"
                required
                leftIcon={
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M20 4H4C2.9 4 2.01 4.9 2.01 6L2 18C2 19.1 2.9 20 4 20H20C21.1 20 22 19.1 22 18V6C22 4.9 21.1 4 20 4ZM20 8L12 13L4 8V6L12 11L20 6V8Z"/>
                  </svg>
                }
              />

              <Input
                label="Telefone"
                name="phone"
                type="tel"
                value={formData.phone}
                onChange={handleInputChange}
                placeholder="(11) 99999-9999"
                leftIcon={
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M6.62 10.79C8.06 13.62 10.38 15.94 13.21 17.38L15.41 15.18C15.69 14.9 16.08 14.82 16.43 14.93C17.55 15.3 18.75 15.5 20 15.5C20.55 15.5 21 15.95 21 16.5V20C21 20.55 20.55 21 20 21C10.61 21 3 13.39 3 4C3 3.45 3.45 3 4 3H7.5C8.05 3 8.5 3.45 8.5 4C8.5 5.25 8.7 6.45 9.07 7.57C9.18 7.92 9.1 8.31 8.82 8.59L6.62 10.79Z"/>
                  </svg>
                }
              />

              <Textarea
                label="Mensagem"
                name="message"
                value={formData.message}
                onChange={handleInputChange}
                placeholder="Escreva sua mensagem aqui..."
                helper="Máximo de 500 caracteres"
                rows={4}
              />

               <div className="flex gap-3 mt-6">
                 <Button
                   type="submit"
                   variant="primary"
                   size="lg"
                   icon={
                     <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                       <path d="M9 16.2L4.8 12L3.4 13.4L9 19L21 7L19.6 5.6L9 16.2Z"/>
                     </svg>
                   }
                 >
                   Enviar Formulário
                 </Button>

                 <Button
                   type="button"
                   variant="secondary"
                   outline
                   onClick={() => setFormData({ name: '', email: '', phone: '', message: '' })}
                 >
                   Limpar
                 </Button>
               </div>
            </form>
          </Card>
        </div>

        {/* Buttons Demo */}
        <div>
          <Card
            title="Componentes de Botões"
            subtitle="Diferentes variações e tamanhos de botões"
            shadow
          >
            <div className="space-y-6">
              <div>
                <h5 className="text-sm font-medium text-gray-900 dark:text-white mb-3">Variações de Cor</h5>
                <div className="flex flex-wrap gap-2">
                  <Button variant="primary">Primary</Button>
                  <Button variant="secondary">Secondary</Button>
                  <Button variant="success">Success</Button>
                  <Button variant="danger">Danger</Button>
                  <Button variant="warning">Warning</Button>
                  <Button variant="info">Info</Button>
                </div>
              </div>

              <div>
                <h5 className="text-sm font-medium text-gray-900 dark:text-white mb-3">Botões Outline</h5>
                <div className="flex flex-wrap gap-2">
                  <Button variant="primary" outline>Primary</Button>
                  <Button variant="success" outline>Success</Button>
                  <Button variant="danger" outline>Danger</Button>
                </div>
              </div>

              <div>
                <h5 className="text-sm font-medium text-gray-900 dark:text-white mb-3">Tamanhos</h5>
                <div className="flex flex-wrap gap-2 items-center">
                  <Button variant="primary" size="sm">Small</Button>
                  <Button variant="primary" size="md">Medium</Button>
                  <Button variant="primary" size="lg">Large</Button>
                </div>
              </div>

              <div>
                <h5 className="text-sm font-medium text-gray-900 dark:text-white mb-3">Com Ícones</h5>
                <div className="flex flex-wrap gap-2">
                  <Button
                    variant="success"
                    icon={
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                        <path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"/>
                      </svg>
                    }
                  >
                    Adicionar
                  </Button>
                  <Button
                    variant="info"
                    icon={
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                        <path d="M3 17.25V21h3.75L17.81 9.94l-3.75-3.75L3 17.25zM20.71 7.04c.39-.39.39-1.02 0-1.41l-2.34-2.34c-.39-.39-1.02-.39-1.41 0l-1.83 1.83 3.75 3.75 1.83-1.83z"/>
                      </svg>
                    }
                  >
                    Editar
                  </Button>
                  <Button
                    variant="danger"
                    icon={
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                        <path d="M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z"/>
                      </svg>
                    }
                  >
                    Excluir
                  </Button>
                </div>
              </div>

              <div>
                <h5 className="text-sm font-medium text-gray-900 dark:text-white mb-3">Estados Especiais</h5>
                <div className="flex flex-wrap gap-2">
                  <Button variant="primary" loading>Carregando...</Button>
                  <Button variant="secondary" disabled>Desabilitado</Button>
                  <Button variant="success" block>Botão Completo</Button>
                </div>
              </div>
            </div>
          </Card>
        </div>
      </div>

      {/* Additional Components Demo */}
      <div className="mb-6">
        <Card
          title="Demonstração de Cards com Diferentes Variações"
          actions={
            <Button
              variant="primary"
              size="sm"
              icon={
                <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
                </svg>
              }
            >
              Ação
            </Button>
          }
          shadow
        >
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <Card className="card-primary" title="Card Primary" shadow>
              <p className="text-sm text-gray-600 dark:text-gray-400">Este é um card com tema primary para destacar informações importantes.</p>
            </Card>
            <Card className="card-success" title="Card Success" shadow>
              <p className="text-sm text-gray-600 dark:text-gray-400">Card de sucesso para mostrar informações positivas ou concluídas.</p>
            </Card>
            <Card className="card-warning" title="Card Warning" shadow>
              <p className="text-sm text-gray-600 dark:text-gray-400">Card de aviso para informações que requerem atenção.</p>
            </Card>
            <Card className="card-danger" title="Card Danger" shadow>
              <p className="text-sm text-gray-600 dark:text-gray-400">Card de perigo para alertas críticos ou erros.</p>
            </Card>
          </div>
        </Card>
      </div>

    </div>
  );
};

export default LayoutDemo;