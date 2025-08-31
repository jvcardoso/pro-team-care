import React, { useState } from 'react';
import { notify } from '../utils/notifications.jsx';
import Card from '../components/ui/Card';
import Button from '../components/ui/Button';
import { CheckCircle, XCircle, AlertCircle, Info, Trash2, HelpCircle, Bell, Zap, Heart, Star, Gift, Coffee } from 'lucide-react';

const NotificationDemo = () => {
  const [counter, setCounter] = useState(0);

  const testSuccess = () => {
    notify.success('Operação realizada com sucesso!');
  };

  const testError = () => {
    notify.error('Ops! Algo deu errado. Tente novamente.');
  };

  const testInfo = () => {
    notify.info('Esta é uma informação importante para você.');
  };

  const testWarning = () => {
    notify.warning('Atenção! Verifique os dados antes de continuar.');
  };

  const testConfirm = () => {
    notify.confirm(
      'Confirmar Ação',
      'Deseja realmente executar esta operação?',
      () => {
        notify.success('Ação confirmada e executada!');
      },
      () => {
        notify.info('Ação cancelada pelo usuário.');
      }
    );
  };

  const testConfirmDelete = () => {
    notify.confirmDelete(
      'Excluir Item',
      'Tem certeza que deseja excluir este item permanentemente?',
      () => {
        notify.success('Item excluído com sucesso!');
      },
      () => {
        notify.info('Exclusão cancelada.');
      }
    );
  };

  const testLongMessage = () => {
    notify.success('Esta é uma mensagem muito longa para testar como o toast se comporta quando há bastante texto para ser exibido. O layout deve se ajustar automaticamente.');
  };

  const testSequence = () => {
    notify.info('Iniciando sequência de testes...');
    
    setTimeout(() => {
      notify.warning('Processando dados...');
    }, 1000);
    
    setTimeout(() => {
      notify.success('Sequência de testes concluída!');
    }, 2000);
  };

  const testCounter = () => {
    const newCounter = counter + 1;
    setCounter(newCounter);
    notify.success(`Contador atualizado: ${newCounter}`);
  };

  const testCustomDuration = () => {
    notify.info('Esta mensagem ficará visível por 10 segundos', { duration: 10000 });
  };

  const testErrorScenarios = () => {
    const scenarios = [
      'Erro de conexão com o servidor',
      'Dados inválidos fornecidos',
      'Permissão negada para esta operação',
      'Tempo limite de requisição excedido',
      'Usuário não autenticado'
    ];
    
    const randomScenario = scenarios[Math.floor(Math.random() * scenarios.length)];
    notify.error(randomScenario);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground flex items-center gap-2">
            <Bell className="h-6 w-6 text-primary" />
            Demonstração de Notificações
          </h1>
          <p className="text-muted-foreground">
            Teste todos os tipos de notificações do sistema
          </p>
        </div>
      </div>

      {/* Botões Básicos */}
      <Card title="🎯 Tipos Básicos de Notificação">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <Button 
            onClick={testSuccess} 
            variant="primary"
            icon={<CheckCircle className="h-4 w-4" />}
            className="bg-green-600 hover:bg-green-700"
          >
            Sucesso
          </Button>
          
          <Button 
            onClick={testError}
            variant="danger"
            icon={<XCircle className="h-4 w-4" />}
          >
            Erro
          </Button>
          
          <Button 
            onClick={testInfo}
            variant="primary"
            icon={<Info className="h-4 w-4" />}
            className="bg-blue-600 hover:bg-blue-700"
          >
            Informação
          </Button>
          
          <Button 
            onClick={testWarning}
            variant="primary"
            icon={<AlertCircle className="h-4 w-4" />}
            className="bg-yellow-600 hover:bg-yellow-700"
          >
            Aviso
          </Button>
        </div>
      </Card>

      {/* Confirmações */}
      <Card title="❓ Modais de Confirmação">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <Button 
            onClick={testConfirm}
            variant="primary"
            icon={<HelpCircle className="h-4 w-4" />}
            className="bg-amber-600 hover:bg-amber-700"
          >
            Confirmação Simples
          </Button>
          
          <Button 
            onClick={testConfirmDelete}
            variant="danger"
            icon={<Trash2 className="h-4 w-4" />}
          >
            Confirmação de Exclusão
          </Button>
        </div>
      </Card>

      {/* Testes Avançados */}
      <Card title="⚡ Testes Avançados">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          <Button 
            onClick={testLongMessage}
            variant="secondary"
            icon={<Zap className="h-4 w-4" />}
          >
            Mensagem Longa
          </Button>
          
          <Button 
            onClick={testSequence}
            variant="secondary"
            icon={<Star className="h-4 w-4" />}
          >
            Sequência de Toasts
          </Button>
          
          <Button 
            onClick={testCounter}
            variant="secondary"
            icon={<Heart className="h-4 w-4" />}
          >
            Contador ({counter})
          </Button>
          
          <Button 
            onClick={testCustomDuration}
            variant="secondary"
            icon={<Coffee className="h-4 w-4" />}
          >
            Duração Personalizada
          </Button>
          
          <Button 
            onClick={testErrorScenarios}
            variant="secondary"
            icon={<Gift className="h-4 w-4" />}
          >
            Cenários Aleatórios
          </Button>
        </div>
      </Card>

      {/* Exemplos de Uso Real */}
      <Card title="💼 Exemplos de Uso Real">
        <div className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            <Button 
              onClick={() => {
                notify.success('Login realizado com sucesso!');
              }}
              variant="primary"
              className="bg-green-600 hover:bg-green-700"
            >
              ✅ Login Bem-sucedido
            </Button>
            
            <Button 
              onClick={() => {
                notify.error('Falha na autenticação. Verifique suas credenciais.');
              }}
              variant="danger"
            >
              ❌ Erro de Login
            </Button>
            
            <Button 
              onClick={() => {
                notify.info('Dados da empresa preenchidos automaticamente!');
              }}
              variant="primary"
              className="bg-blue-600 hover:bg-blue-700"
            >
              ℹ️ CNPJ Consultado
            </Button>
            
            <Button 
              onClick={() => {
                notify.warning('Preencha todos os campos obrigatórios.');
              }}
              variant="primary"
              className="bg-yellow-600 hover:bg-yellow-700"
            >
              ⚠️ Validação de Form
            </Button>
            
            <Button 
              onClick={() => {
                notify.confirmDelete(
                  'Excluir Empresa',
                  'Tem certeza que deseja excluir a empresa "Exemplo LTDA"?',
                  () => notify.success('Empresa excluída com sucesso!'),
                  () => notify.info('Exclusão cancelada.')
                );
              }}
              variant="danger"
            >
              🗑️ Excluir Empresa
            </Button>
            
            <Button 
              onClick={() => {
                notify.confirm(
                  'Salvar Alterações',
                  'Deseja salvar as alterações feitas no formulário?',
                  () => notify.success('Alterações salvas com sucesso!'),
                  () => notify.warning('Alterações descartadas.')
                );
              }}
              variant="primary"
              className="bg-amber-600 hover:bg-amber-700"
            >
              💾 Salvar Form
            </Button>
          </div>
        </div>
      </Card>

      {/* Instruções */}
      <Card title="📋 Como Usar" className="bg-blue-50 dark:bg-blue-900/20">
        <div className="space-y-4 text-sm">
          <div>
            <h4 className="font-medium text-foreground mb-2">Importação:</h4>
            <code className="bg-gray-100 dark:bg-gray-800 p-2 rounded block text-xs">
              import {`{ notify }`} from '../utils/notifications.jsx';
            </code>
          </div>
          
          <div>
            <h4 className="font-medium text-foreground mb-2">Uso Básico:</h4>
            <div className="space-y-1 font-mono text-xs bg-gray-100 dark:bg-gray-800 p-3 rounded">
              <div>notify.success('Mensagem de sucesso');</div>
              <div>notify.error('Mensagem de erro');</div>
              <div>notify.info('Mensagem informativa');</div>
              <div>notify.warning('Mensagem de aviso');</div>
            </div>
          </div>
          
          <div>
            <h4 className="font-medium text-foreground mb-2">Confirmações:</h4>
            <div className="space-y-1 font-mono text-xs bg-gray-100 dark:bg-gray-800 p-3 rounded">
              <div>notify.confirm('Título', 'Mensagem', onConfirm, onCancel);</div>
              <div>notify.confirmDelete('Título', 'Mensagem', onDelete);</div>
            </div>
          </div>
        </div>
      </Card>
    </div>
  );
};

export default NotificationDemo;